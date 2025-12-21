frappe.ui.form.on('Attendance', { 
    refresh(frm) {
      const field = frm.get_field("custom_html");
      if (!field) return;
  
      const wrapper = field.$wrapper;
      const base64_image = frm.doc.image_data; // Base64 string
      if (base64_image) {
        wrapper.html(`
          <img src="${base64_image}" style="max-width: 200px;max-height: 200px;border-radius: 8px;border: 1px solid #ccc;"/>
        `);
      } else {
        wrapper.html(`<p>No photo uploaded yet</p>`);
      }
    }
  });
  