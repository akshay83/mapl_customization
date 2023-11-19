from __future__ import unicode_literals
import frappe
import json
from frappe.utils import flt, getdate

def execute(filters=None):
    columns, data = [], []
    report_type = filters.get("document_type") or "Purchase Summary"
    dt = "Purchase" if "Purchase" in report_type else "Sales"
    report = TaxesReport(dt, filters.get("from_date"), filters.get("to_date"), report_type)
    #columns.extend(get_columns(filter))
    data = report.get_data()
    columns = extract_columns(data) if len(data) > 0 else []
    return columns, data

class TaxesReport():
    def __init__(self, doctype, from_date, to_date, report_type):
        self.doctype = doctype
        self.from_date = from_date
        self.to_date = to_date
        self.party_type = "Customer" if (self.doctype=="Sales") else "Supplier"
        self.report_type = report_type

    def get_dump_query(self):
        dump_query = """
                    select
                            item.parent as `Name:Link/{doctype} Invoice:125`,
                            doc.reporting_name as `Reporting Name:Data:100`,
                            doc.posting_date as `Posting Date:Date:100`,  
                            {doc_columns},
                            (select b_addr.gstin from `tabAddress` b_addr use index (address_title)
                                where b_addr.address_title=party.name and b_addr.name=doc.{address_column}_address) as `Billing GSTIN:Data:125`,
                            addr.gstin as `Shipping GSTIN:Data:100`,
                            addr.city as `Shipping City:Data:100`,
                            addr.state as `Shipping State:Data:125`,
                            addr.gst_state_number as `GST State Code:Int:50`,
                            item.item_code as `Item Code:Link/Item:100`,
                            item.description as `Description:Data:150`,
                            item.item_group as `Item Group:Link/Item Group:75`,
                            item.gst_hsn_code as `HSN Code:Data:75`,
                            item.item_tax_rate as `Item Tax Rate:Data:100`,
                            cast(left(right(item.item_tax_rate,5),4) as decimal(5,2)) as `Tax Rate Alt:Float:50`,
                            cast(mid(item.item_tax_rate,locate(':',item.item_tax_rate,locate('IGST',item.item_tax_rate))+1,5) as decimal(5,2)) as `Tax Rate:Float:50`,
                            sum(item.qty) as `Qty:Float:50`,
                            cast(avg(item.net_rate) as decimal(17,2)) as `Net Rate:Currency:100`,   
                            cast(sum(item.net_amount) as decimal(17,2)) as `Net Amount:Currency:100`,   
                            
                            (((gst_state_number<>0 and gst_state_number<>23) or
                            ((gstin is not null and gstin<>'' and left(gstin,2)<>23) or
                            (state is not null and state not regexp ('MADHYA PRADESH|M.P.|M.P|MP')) and
                            (state is not null and state<>''))) or left(place_of_supply,2)<>'23') as flag
                        from
                            `tab{doctype} Invoice Item` item use index (parent),
                            `tab{doctype} Invoice` doc use index (PRIMARY),
                            `tabAddress` addr,
                            `tab{partytype}` party use index (PRIMARY)
                        where
                            doc.docstatus=1
                            and doc.name=item.parent
                            and addr.address_title=party.name
                            and doc.posting_date between '{from_date}' and '{to_date}'
                            and doc.name in (select parent from `tab{doctype} Taxes and Charges` taxes where taxes.account_head regexp ('SGST|CGST|IGST') {additional_tax_conditions})
                            {doc_specific_conditions}
                        group by
                            item.gst_hsn_code,  
                            item.parent,
                            `Tax Rate:Float:50`
                        order by
                            doc.name,
                            doc.posting_date
        """
        dump_query = dump_query.format(**{
                    "doctype":self.doctype,
                    "partytype": self.party_type,
                    "additional_tax_conditions": self.get_additional_tax_conditions(),
                    "doc_specific_conditions": self.get_document_specific_conditions(),
                    "address_column": self.party_type.lower(),
                    "doc_columns": self.get_document_specific_columns(),
                    "from_date": self.from_date,
                    "to_date": self.to_date
                    })
        return dump_query
    
    def get_query(self):
        dump_query = self.get_dump_query()
        query = """
                    select *,
                        cast((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100) as decimal(17,2)) as `Total Tax:Currency:100`,
                        if(flag,cast((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100) as decimal(17,2)),0) as `IGST:Currency:100`,
                        if(flag,0,cast(((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100)/2) as decimal(17,2))) as `SGST:Currency:100`,
                        if(flag,0,cast(((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100)/2) as decimal(17,2))) as `CGST:Currency:100`
                    from (
                        {dump_query}
                    ) a
        """.format(**{"dump_query":dump_query})
        
        if "Summary" in self.report_type:
            query = """
                    select 
                        `Name:Link/{doctype} Invoice:125`,
                        `Reporting Name:Data:100`,
                        `Bill No:Data:100`,                        
                        `Posting Date:Date:100`,
                        `Bill Date:Date:100`,
                        `{partytype} Name:Data:125`,
                        `Billing GSTIN:Data:125`,
                        `Shipping GSTIN:Data:100`,
                        `Shipping City:Data:100`,
                        `Shipping State:Data:125`,
                        `GST State Code:Int:50`,
                        sum(`Net Amount:Currency:100`) as `Taxable Amount:Currency:100`,
                        sum(cast((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100) as decimal(17,2))) as `Total Tax:Currency:100`,

                        sum(if(flag=1 and `Tax Rate:Float:50`=5,cast((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100) as decimal(17,2)),0)) as `IGST-5%:Currency:100`,
                        sum(if(flag=1 and `Tax Rate:Float:50`=12,cast((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100) as decimal(17,2)),0)) as `IGST-12%:Currency:100`,
                        sum(if(flag=1 and `Tax Rate:Float:50`=18,cast((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100) as decimal(17,2)),0)) as `IGST-18%:Currency:100`,
                        sum(if(flag=1 and `Tax Rate:Float:50`=28,cast((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100) as decimal(17,2)),0)) as `IGST-28%:Currency:100`,

                        sum(if(flag=0 and `Tax Rate:Float:50`=5,cast(((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100)/2) as decimal(17,2)),0)) as `SGST-2.5%:Currency:100`,
                        sum(if(flag=0 and `Tax Rate:Float:50`=12,cast(((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100)/2) as decimal(17,2)),0)) as `SGST-6%:Currency:100`,
                        sum(if(flag=0 and `Tax Rate:Float:50`=18,cast(((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100)/2) as decimal(17,2)),0)) as `SGST-9%:Currency:100`,
                        sum(if(flag=0 and `Tax Rate:Float:50`=28,cast(((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100)/2) as decimal(17,2)),0)) as `SGST-14%:Currency:100`,
                  
                        sum(if(flag=0 and `Tax Rate:Float:50`=5,cast(((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100)/2) as decimal(17,2)),0)) as `CGST-2.5%:Currency:100`,
                        sum(if(flag=0 and `Tax Rate:Float:50`=12,cast(((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100)/2) as decimal(17,2)),0)) as `CGST-6%:Currency:100`,
                        sum(if(flag=0 and `Tax Rate:Float:50`=18,cast(((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100)/2) as decimal(17,2)),0)) as `CGST-9%:Currency:100`,
                        sum(if(flag=0 and `Tax Rate:Float:50`=28,cast(((`Net Amount:Currency:100`*`Tax Rate:Float:50`/100)/2) as decimal(17,2)),0)) as `CGST-14%:Currency:100`
                    from ( 
                        {dump_query}
                    ) a 
                    group by 
                        `Name:Link/{doctype} Invoice:125`
                    order by
                        `Bill Date:Date:100`,
                        `Posting Date:Date:100`,
                        `Name:Link/{doctype} Invoice:125`
            """.format(**{
                "dump_query": dump_query,
                "doctype": self.doctype,
                "partytype": self.party_type
            })
        
        print (query)
        return query
    
    def generate_raw_data(self):        
        self.raw_data = frappe.db.sql(self.get_query(), as_dict=1)

    def get_document_specific_conditions(self):
        if self.doctype == "Purchase":
                return "and doc.supplier_address=addr.name"
        return "and doc.shipping_address_name=addr.name"

    def get_additional_tax_conditions(self):
        if self.doctype == "Purchase":
            return "and tax_amount<>0"
        return ""

    def get_document_specific_columns(self):
        if self.doctype == "Purchase":
                return "doc.bill_no as `Bill No:Data:100`, doc.bill_date as `Bill Date:Date:100`, doc.supplier_name as `Supplier Name:Data:125`"
        return "doc.customer_name as `Customer Name:Data:125`, doc.special_invoice as `Special Invoice:Data:100`, doc.place_of_supply as `Place of Supply:Data:75`"
    
    def do_post_fetch_calculations(self):
        for row in self.raw_data:
            billing_gstin = row.get("Billing GSTIN:Data:125")
            shipping_gstin = row.get("Shipping GSTIN:Data:100")
            shipping_state = row.get("Shipping State:Data:125") 
            state_code = int(row.get("GST State Code:Int:50"))
            special_invoice = row.get("Special Invoice:Data:100")
            urp = True if (not billing_gstin and not shipping_gstin) else False

            #--DEBUG--row["billing_gstin:Data:100"] = billing_gstin[:2] if billing_gstin else None
            #--DEBUG--row["billing_gstin flag:Data:100"] = (billing_gstin and billing_gstin[:2] not in ("","23"))
            #--DEBUG--row["shipping_state:Data:100"] = shipping_state.lower().strip() if shipping_state else ""
            #--DEBUG--row["shipping_state flag:Data:100"] = (shipping_state and shipping_state.lower().strip() != "madhya pradesh")

            gstin_check = "Out of M.P."
            if not urp and (billing_gstin and billing_gstin[:2] == "23"):
                gstin_check = "In M.P."
            elif urp and (shipping_state and shipping_state.lower().strip() != "madhya pradesh"):
                gstin_check = "Out of M.P."
            elif urp and not (shipping_state and shipping_state.lower().strip() != "madhya pradesh"):
                gstin_check = "In M.P."

            state_number_check="Out of M.P." if state_code!=0 and state_code!=23 else "In M.P."

            #--DEBUG--gstin_check = "Out of M.P." if ((billing_gstin and billing_gstin[:2] not in ("","23")) \
            #                    and (shipping_state and shipping_state.lower() != "madhya pradesh")) else "In M.P."
            #--DEBUG--gst_state = "Out of M.P." if (billing_gstin and billing_gstin[:2] not in ("","23")) else "In M.P."            

            #--DEBUG--state_check = "In M.P."
            #--DEBUG--if (gstin_check != "In M.P."):
            #--DEBUG--    state_check = "Out of M.P."
            #--DEBUG--elif (shipping_state and shipping_state.lower().strip() not in ("","m.p.","madhya pradesh","mp")):
            #--DEBUG--    state_check = "Out of M.P."

            gst_check = "Error"
            #--DEBUG--if (gstin_check == state_check == state_number_check):
            if (gstin_check == state_number_check):
                gst_check = "OK"

            if special_invoice and special_invoice[:3].lower() == "sez":
                final_state = "SEZ Supply"
            elif gst_check == "OK":
                final_state = gstin_check #Any One Column out of 3 that passed gst_check as "OK"
            else:
                final_state = "ERROR"

            if (final_state == "SEZ Supply"):
                row["Total Tax:Currency:100"] = row["SGST:Currency:100"] = row["IGST:Currency:100"] = row["CGST:Currency:100"] = 0
            row["Invoice Total:Currency:125"] = row["Net Amount:Currency:100"] + row["SGST:Currency:100"] + row["IGST:Currency:100"] + row["CGST:Currency:100"]

            row["gstin_check"]=gstin_check
            #--DEBUG--row["state_check"]=state_check
            row["state_number_check"]=state_number_check

            row["GST Check:Data:75"]=gst_check
            row["Final State:Data:100"]=final_state
            row["Dealer Type:Data:100"]="Regd Dealer" if (billing_gstin and billing_gstin!="") else "Un-Regd Dealer"
            final_state_code = 23
            if final_state != "In M.P.":
                final_state_code = billing_gstin[:2] if billing_gstin else "Error"
            row["State Code:Data:50"]=final_state_code
            row["Check GSTIN:Data:75"]="Error" if billing_gstin!=shipping_gstin else "OK"

    def get_data(self):
        self.generate_raw_data()
        if self.doctype == "Sales":
            self.do_post_fetch_calculations()
        return self.raw_data

def extract_columns(query_result):
    list_keys = query_result[0].keys()
    columns = []
    for key in list_keys:
        broken_key = key.split(":")
        link = None
        try:
            link = broken_key[1].split("/")
        except:
            pass
        columns.append({
			"fieldname":key,
			"label":broken_key[0],
			"fieldtype:":link[0] if link else "Data",
            "options": link[1] if (link and len(link)>1) else None,
			"width": broken_key[2] if len(broken_key)>1 else 100,
            "default": 0 if (link and link[0].lower() in ("currency","float")) else None
        })
    #--DEBUG--print (columns)
    return columns
        