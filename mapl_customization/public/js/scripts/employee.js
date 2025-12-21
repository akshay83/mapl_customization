frappe.ui.form.on("Employee", "generate_code", function(frm) {
	if (!frappe.user.has_role("System Manager", "HR Manager")) {
		frappe.msgprint("Not Permitted");
		return;
	}
  if (frm.doc.registration_code !== undefined && frm.doc.registration_code != "") {
    frm.set_value('registration_code', null).then(() => {
      frm.refresh_field('registration_code'); // Ensure the UI element updates
      frm.get_field("generate_code").set_label("Generate Code");
      frm.refresh_field('generate_code');
    });    
    //frappe.db.set_value("Employee", frm.doc.name, "registration_code", null);  
  } else {
    frm.set_value('registration_code', getRandomInt(100001,999999)).then(() => {
      frm.refresh_field('registration_code'); // Ensure the UI element updates
      frm.refresh_field('generate_code');
    });
    //frappe.db.set_value("Employee", frm.doc.name, "registration_code", getRandomInt(1,999999));
  }
  //frappe.db.commit();
  //cur_frm.reload_doc();
  console.log("Saving/Clearing Code");
  frm.save();
});

frappe.ui.form.on('Employee', "refresh", function(frm) { 
      const code_field = frm.get_field("registration_code");
      if (code_field && (frm.doc.registration_code !== undefined && frm.doc.registration_code != "")) {
        console.log("Changing Button Label");
        frm.get_field("generate_code").set_label("Clear Code");
      }
      const field = frm.get_field("custom_html");
      if (!field) return;
  
      const wrapper = field.$wrapper;
      const base64_image = frm.doc.face_detector_image; // Base64 string
      if (base64_image) {
        wrapper.html(`<div style="margin-top:3px;">Registered Face for Attendance</div>
          <img src="${base64_image}" style="max-width: 200px;max-height: 200px;border-radius: 8px;border: 1px solid #ccc;margin:5px;"/>
        `);
      } else {
        wrapper.html(`<p>No photo uploaded yet</p>`);
      }
});

function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}