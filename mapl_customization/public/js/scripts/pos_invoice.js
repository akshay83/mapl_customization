frappe.ui.form.on('POS Invoice', {
	onload(frm) {
	    if ($(window).width() < 999 && frappe.user.has_role("POS User") && !frappe.user.has_role("System User")) {
	        $(".standard-actions.flex").detach().appendTo(".collapse.navbar-collapse.justify-content-end");
	        $(".btn.btn-primary.btn-sm.primary-action").detach().appendTo(".collapse.navbar-collapse.justify-content-end");
	        $(".standard-actions.flex").css({"margin-left":"20px"})
	    }
		    $(`<style type='text/css'> 
		        @media screen and (max-width:999px) {		    
		            .container.page-body {
    		            width: 100% !important;
		                max-width: initial;
		            }
    		        .page-head.flex {
		                display:none;
		            }
		            .navbar {
    		            height: 40px !important;
		            }
		            .search-bar {
    		            display: none !important;    
		            }
		        }
		        .highlighted-numpad-btn { 
		            background-color:cadetblue !important;
		        } 
		        @media screen and (max-width: 999px) {
		            .point-of-sale-app > .item-details-container {
                        top: 20% !important;
                        left: 25% !important;
                        height: 380px !important;
                        max-height: 380px !important;
                        width: 400px !important;
		            }
		        }
		        @media screen and (min-width: 1281px) {
		            .point-of-sale-app > .item-details-container {
                        top: 20% !important;
                        left: 25% !important;
                        height: 400px !important;
                        max-height: 400px !important;
                        width: 500px !important;
		            }
		        }
		        @media screen and (min-width: 1000px) and (max-width:1280px) {
		            .point-of-sale-app > .item-details-container {
                        top: 25% !important;
                        left: 25% !important;
                        height: 400px !important;
                        max-height: 400px !important;
                        width: 500px !important;
		            }
		        }
		        .point-of-sale-app > .item-details-container {
		            position:absolute !important;
		            z-index: 1200 !important;
                    transform: translate(-50%, -50%) !important;
                    box-shadow:  0px 0px 5px 5px #aaa !important;
                    min-height: 100px !important;
		        }
		        .point-of-sale-app > .items-selector {
		            grid-column: span 6/span 6 !important;
		        }
		        .point-of-sale-app > .items-selector > .items-container {
		            grid-template-columns: repeat(3,minmax(0,1fr)) !important;
		        }
		        @media screen and (max-width: 999px) {
		            .point-of-sale-app > .customer-cart-container > .cart-container > .abs-cart-container > .numpad-section {
		                position:absolute !important;
                        bottom: 35% !important;
                        right: 10% !important;
                        width: 400px;
                        height: 380px !important;
		            }
		        }
		        @media screen and (min-width: 1281px) {
		            .point-of-sale-app > .customer-cart-container > .cart-container > .abs-cart-container > .numpad-section {
		                position:absolute !important;
                        bottom: 20% !important;
                        right: 10% !important;
                        width: 500px;
                        height: 400px !important;
		            }
		        }
		        @media screen and (min-width: 1000px) and (max-width:1280px) {
		            .point-of-sale-app > .customer-cart-container > .cart-container > .abs-cart-container > .numpad-section {
		                position:absolute !important;
                        bottom: 20% !important;
                        right: 5% !important;
                        width: 500px;
                        height: 400px !important;
		            }
		        }
		        
		        .point-of-sale-app > .customer-cart-container > .cart-container > .abs-cart-container > .numpad-section {
		            z-index: 1200 !important;
                    /*transform: translate(-50%, -50%) !important;*/
                    box-shadow:  0px 0px 5px 5px #aaa !important;
                    background-color: var(--fg-color);
                    border-radius: var(--border-radius-md);
                    border: 1px solid blue;
                    padding: var(--padding-lg);
                    padding-top: var(--padding-md);                    
		        }
		        .custom-close-btn {
		            padding: var(--padding-sm);
                    border-radius: var(--border-radius-md);
                    font-size: var(--text-lg);
                    font-weight: 700;
                    margin: 0;
                    margin-bottom: var(--margin-sm);
                    color: #fff;
                    background-color: var(--blue-500);
                    align-items: center;
                    justify-content: center;    
                    display: flex;
                    cursor: pointer;
		        }
		        .mode-of-payment-control {
		            display: none !important;
		        }
		        .cash-shortcuts {
		            display: none !important;
		        }
		        .mode-of-payment > .pay-amount {
		            display: inline !important;
		        }
		        .mode-of-payment.border-primary {
		            background-color: lightblue !important;
		        }
		        .point-of-sale-app>.payment-container>.payment-modes>.payment-mode-wrapper {
		            min-width: 30% !important;
		        }
		        .point-of-sale-app>.payment-container>.fields-numpad-container>.number-pad {
		            display: grid !important;
                    justify-content: initial !important;
                    align-items: initial !important;
		        }
		        </style>`).appendTo("head");
		frm.doc.update_stock = 0;
		$(".cart-container .cart-items-section").click(function() {
		    if ( ($(".payment-container").attr('style') == 'display: none;') || ($(".payment-container").attr('style') === undefined) ) {
		    $(".item-details-container").find(`[data-fieldname='uom']`).hide();
		    $(".item-details-container").find(`[data-fieldname='warehouse']`).hide();
		    $(".item-details-container").find(`[data-fieldname='conversion_factor']`).hide();
		    $(".item-details-container").find(`[data-fieldname='actual_qty']`).hide();
		    $(".item-details-container").find(`[data-fieldname='qty']`).find('.control-value.like-disabled-input').css('display','block');
		    $(".item-details-container").find(`[data-fieldname='qty']`).find(".control-input").css('display','none');
		    $(".item-details-container").find(`[data-fieldname='rate']`).find('.control-value.like-disabled-input').css('display','block');
		    $(".item-details-container").find(`[data-fieldname='rate']`).find(".control-input").css('display','none');
		    $(".item-details-container").find(`[data-fieldname='discount_percentage']`).find('.control-value.like-disabled-input').css('display','block');
		    $(".item-details-container").find(`[data-fieldname='discount_percentage']`).find(".control-input").css('display','none');
		    $(".numpad-section").find(".numpad-btn.checkout-btn").hide();
		    frappe.dom.freeze();
		    }
		});
		if ($(".numpad-section").has($(".custom-close-btn")).length===0) {
            $(".numpad-section").append(`<div class="custom-close-btn">Close</div>`);
		}
		$(".close-btn").click(function() {
		    frappe.dom.unfreeze();		     
		});
		$(".numpad-container").find(".numpad-btn.col-span-2.remove-btn").click(function() {
		    frappe.dom.unfreeze();		     
		});
		$(".numpad-container").find(".numpad-btn.col-span-2").click(function() { 
		    $(".numpad-container").find(".highlighted-numpad-btn").removeClass("highlighted-numpad-btn")
		});
		$(".numpad-section").find(".custom-close-btn").click(function() {
		    $(".close-btn").trigger("click");
		});
		//Following Code Handles Error during Numbpad and Mode of Payment Interactions
		$(".number-pad").click(function() {
		    setTimeout(function() {
		        if (cur_pos.payment.selected_mode && (typeof cur_pos.payment.selected_mode !== undefined)) {
    		        let mode = cur_pos.payment.selected_mode.df.label.replace(/ +/g, "_").toLowerCase();
		            $(".payment-mode-wrapper").find(`div.mode-of-payment[data-mode='${mode}']`).addClass('border-primary');
		        }
		        $(".mode-of-payment").click(function(e) {
		            if (cur_pos.payment.selected_mode && (typeof cur_pos.payment.selected_mode !== undefined)) {
		                if (cur_pos.payment.selected_mode.df.label.replace(/ +/g, "_").toLowerCase() != e.target.getAttribute("data-mode").toLowerCase()) {
    		                cur_pos.payment.numpad_value = "";
		                }
		            }
		        });
		    }, 300);
		});
		cur_pos.payment.numpad_value = "";
	},
	before_submit(frm) {
	    if (frm.doc.total > frm.doc.paid_amount) {
	        frappe.msgprint(__('Paid Amount is Less Than the Total Amount'));
			frappe.validated = false;
	    }
	}
});