#!/usr/bin/env python

from SettingsWidgets import *
from gi.repository import AccountsService, GLib
import PAM
import pexpect
import time
from random import randint
import shutil
import PIL
import os

class Module:
    def __init__(self, content_box):
        keywords = _("user, account, information, details")
        sidePage = SidePage(_("Account details"), "cs-user", keywords, content_box, 200, module=self)
        self.sidePage = sidePage
        self.name = "user"
        self.category = "prefs"
        self.comment = _("Change your user preferences and password")                        

    def on_module_selected(self, switch_container):
        if not self.loaded:
            print "Loading User module"
       
            self.face_button = PictureChooserButton(num_cols=4, button_picture_size=96, menu_pictures_size=64)
            self.face_button.set_alignment(0.0, 0.5)
            self.face_button.set_tooltip_text(_("Click to change your picture"))

            self.face_photo_menuitem = Gtk.MenuItem.new_with_label(_("Take a photo..."))
            self.face_photo_menuitem.connect('activate', self._on_face_photo_menuitem_activated)         

            self.face_browse_menuitem = Gtk.MenuItem.new_with_label(_("Browse for more pictures..."))       
            self.face_browse_menuitem.connect('activate', self._on_face_browse_menuitem_activated)
           
            face_dirs = ["/usr/share/cinnamon/faces"]
            for face_dir in face_dirs:
                if os.path.exists(face_dir):                    
                    pictures = sorted(os.listdir(face_dir))
                    for picture in pictures:
                        path = os.path.join(face_dir, picture)
                        self.face_button.add_picture(path, self._on_face_menuitem_activated)
           
            self.realname_entry = EditableEntry()
            self.realname_entry.connect("changed", self._on_realname_changed)
            self.realname_entry.set_tooltip_text(_("Click to change your name"))
            
            table = Gtk.Table.new(3, 2, False)
            table.set_row_spacings(8)
            table.set_col_spacings(15)        
            self.sidePage.add_widget(table)
            
            label_picture = Gtk.Label.new(_("Picture:"))
            label_picture.set_alignment(1, 0.5)
            label_picture.get_style_context().add_class("dim-label")
            table.attach(label_picture, 0, 1, 0, 1)

            password_mask = Gtk.Label.new(u'\u2022\u2022\u2022\u2022\u2022\u2022')        
            password_mask.set_alignment(0.0, 0.5)
            self.password_button = Gtk.Button()
            self.password_button.add(password_mask)
            self.password_button.set_relief(Gtk.ReliefStyle.NONE)
            self.password_button.set_tooltip_text(_("Click to change your password"))
            self.password_button.connect('activate', self._on_password_button_clicked)
            self.password_button.connect('released', self._on_password_button_clicked)
            
            label_name = Gtk.Label.new(_("Name:"))
            label_name.set_alignment(1, 0.5)
            label_name.get_style_context().add_class("dim-label")                        
            table.attach(label_name, 0, 1, 1, 2)

            label_name = Gtk.Label.new(_("Password:"))
            label_name.set_alignment(1, 0.5)
            label_name.get_style_context().add_class("dim-label")                        
            table.attach(label_name, 0, 1, 2, 3)
            
            box = Gtk.Box()
            box.pack_start(self.face_button, False, False, 0)        
            table.attach(box, 1, 2, 0, 1, xoptions=Gtk.AttachOptions.EXPAND|Gtk.AttachOptions.FILL)
            table.attach(self.realname_entry, 1, 2, 1, 2, xoptions=Gtk.AttachOptions.EXPAND|Gtk.AttachOptions.FILL)
            table.attach(self.password_button, 1, 2, 2, 3, xoptions=Gtk.AttachOptions.EXPAND|Gtk.AttachOptions.FILL)        

            current_user = GLib.get_user_name()
            self.accountService = AccountsService.UserManager.get_default().get_user(current_user)
            self.accountService.connect('notify::is-loaded', self.load_user_info)       

            self.face_button.add_separator()

            webcam_detected = False
            try:
                import cv
                capture = cv.CaptureFromCAM(-1)
                for i in range(10):
                    img = cv.QueryFrame(capture)
                    if img != None:
                        webcam_detected = True
            except Exception, detail:
                print detail

            if (webcam_detected):
                self.face_button.add_menuitem(self.face_photo_menuitem)
                self.face_button.add_menuitem(self.face_browse_menuitem)
            else:
                self.face_button.add_menuitem(self.face_browse_menuitem)
    
    def update_preview_cb (self, dialog, preview):
        filename = dialog.get_preview_filename()        
        dialog.set_preview_widget_active(False)
        if filename is not None and os.path.isfile(filename):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename, 128, 128)
                if pixbuf is not None:      
                    preview.set_from_pixbuf (pixbuf)      
                    dialog.set_preview_widget_active(True)                            
            except:
                pass
    
    def _on_face_photo_menuitem_activated(self, menuitem):
        try:
            import cv
            capture = cv.CaptureFromCAM(-1)
            for i in range(10):
                img = cv.QueryFrame(capture)
                if img is not None:
                    path = "/tmp/cinnamon-webcam.png"
                    cv.SaveImage(path, img)
                    image = PIL.Image.open(path)            
                    width, height = image.size            
                    if width > height:
                        new_width = height
                        new_height = height
                    elif height > width:
                        new_width = width
                        new_height = width
                    else:
                        new_width = width
                        new_height = height
                    left = (width - new_width)/2
                    top = (height - new_height)/2
                    right = (width + new_width)/2
                    bottom = (height + new_height)/2            
                    image = image.crop((left, top, right, bottom))
                    image.thumbnail((96, 96), Image.ANTIALIAS)            
                    face_path = os.path.join(self.accountService.get_home_dir(), ".face")
                    image.save(face_path, "png")
                    self.accountService.set_icon_file(face_path)
                    self.face_button.set_picture_from_file(face_path)                    
        except Exception, detail:
            print detail

    def _on_face_browse_menuitem_activated(self, menuitem):
        dialog = Gtk.FileChooserDialog(None, None, Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_current_folder(self.accountService.get_home_dir())
        filter = Gtk.FileFilter()
        filter.set_name(_("Images"))
        filter.add_mime_type("image/*")
        dialog.add_filter(filter)
        
        preview = Gtk.Image()
        dialog.set_preview_widget(preview);
        dialog.connect("update-preview", self.update_preview_cb, preview)
        dialog.set_use_preview_label(False)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            path = dialog.get_filename()
            image = PIL.Image.open(path)            
            width, height = image.size            
            if width > height:
                new_width = height
                new_height = height
            elif height > width:
                new_width = width
                new_height = width
            else:
                new_width = width
                new_height = height
            left = (width - new_width)/2
            top = (height - new_height)/2
            right = (width + new_width)/2
            bottom = (height + new_height)/2            
            image = image.crop((left, top, right, bottom))
            image.thumbnail((96, 96), Image.ANTIALIAS)            
            face_path = os.path.join(self.accountService.get_home_dir(), ".face")
            image.save(face_path, "png")
            self.accountService.set_icon_file(face_path)
            self.face_button.set_picture_from_file(face_path)            

        dialog.destroy()

    def _on_face_menuitem_activated(self, path):
        if os.path.exists(path):
            self.accountService.set_icon_file(path)            
            shutil.copy(path, os.path.join(self.accountService.get_home_dir(), ".face"))
            return True

    def load_user_info(self, user, param):
        self.realname_entry.set_text(user.get_real_name())
        for path in [os.path.join(self.accountService.get_home_dir(), ".face"), user.get_icon_file(), "/usr/share/cinnamon/faces/user-generic.png"]:
            if os.path.exists(path):
                self.face_button.set_picture_from_file(path)
                break

    def _on_realname_changed(self, widget, text):
        self.accountService.set_real_name(text)       

    def _on_password_button_clicked(self, widget):        
        dialog = PasswordDialog()                
        response = dialog.run()
                            

class PasswordDialog(Gtk.Dialog):

    def __init__ (self):            
        super(PasswordDialog, self).__init__()
        
        self.correct_current_password = False # Flag to remember if the current password is correct or not        

        self.set_modal(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_title("")

        table = Gtk.Table(6, 3)
        table.set_border_width(6)
        table.set_row_spacings(8)
        table.set_col_spacings(15)        

        label = Gtk.Label.new(_("Current password"))
        label.set_alignment(1, 0.5)
        table.attach(label, 0, 1, 0, 1)

        label = Gtk.Label.new(_("New password"))
        label.set_alignment(1, 0.5)
        table.attach(label, 0, 1, 1, 2)

        label = Gtk.Label.new(_("Confirm password"))
        label.set_alignment(1, 0.5)
        table.attach(label, 0, 1, 3, 4)

        self.current_password = Gtk.Entry()
        self.current_password.set_visibility(False)
        self.current_password.connect("focus-out-event", self._on_current_password_changed)
        table.attach(self.current_password, 1, 3, 0, 1)

        self.new_password = Gtk.Entry()        
        self.new_password.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "reload")
        self.new_password.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("Generate a password"))
        self.new_password.connect("icon-release", self._on_new_password_icon_released)
        self.new_password.connect("changed", self._on_passwords_changed)
        table.attach(self.new_password, 1, 3, 1, 2)

        self.strengh_indicator = Gtk.ProgressBar()
        self.strengh_indicator.set_tooltip_text(_("Your new password needs to be at least 8 characters long"))
        self.strengh_indicator.set_fraction(0.0)
        table.attach(self.strengh_indicator, 1, 2, 2, 3, xoptions=Gtk.AttachOptions.EXPAND|Gtk.AttachOptions.FILL)                
        self.strengh_indicator.set_size_request(-1, 1)

        self.strengh_label = Gtk.Label()
        self.strengh_label.set_tooltip_text(_("Your new password needs to be at least 8 characters long"))
        self.strengh_label.set_alignment(1, 0.5)
        table.attach(self.strengh_label, 2, 3, 2, 3)

        self.confirm_password = Gtk.Entry()
        self.confirm_password.connect("changed", self._on_passwords_changed)
        table.attach(self.confirm_password, 1, 3, 3, 4)

        self.show_password = Gtk.CheckButton(_("Show password"))
        self.show_password.connect('toggled', self._on_show_password_toggled)
        table.attach(self.show_password, 1, 3, 4, 5)

        self.infobar = Gtk.InfoBar()
        self.infobar.set_message_type(Gtk.MessageType.ERROR)
        label = Gtk.Label.new(_("An error occured. Your password was not changed."))
        content = self.infobar.get_content_area()
        content.add(label)        
        table.attach(self.infobar, 0, 3, 5, 6)

        self.set_border_width(6)       
        
        box = self.get_content_area()
        box.add(table)
        self.show_all()

        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, _("Change"), Gtk.ResponseType.OK, )

        self.set_passwords_visibility()
        self.set_response_sensitive(Gtk.ResponseType.OK, False)
        self.infobar.hide()

        self.connect("response", self._on_response)

    def _on_response(self, dialog, response_id):        
        if response_id == Gtk.ResponseType.OK:
            self.change_password()
        else:
            self.destroy()

    def change_password(self):
        oldpass = self.current_password.get_text()
        newpass = self.new_password.get_text()        
        passwd = pexpect.spawn("/usr/bin/passwd")
        time.sleep(0.5)
        passwd.sendline(oldpass)
        time.sleep(0.5)
        passwd.sendline(newpass)
        time.sleep(0.5)
        passwd.sendline(newpass)
        time.sleep(0.5)
        passwd.close()
                
        if passwd.exitstatus is None or passwd.exitstatus > 0:                            
            self.infobar.show()
        else:
            self.destroy()            

    def set_passwords_visibility(self):
        visible = self.show_password.get_active()       
        self.new_password.set_visibility(visible)
        self.confirm_password.set_visibility(visible)
        
    def _on_new_password_icon_released(self, widget, icon_pos, event):
        self.infobar.hide()
        self.show_password.set_active(True)        
        characters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-"
        newpass = ""
        for i in range (8):
            index = randint(0, len(characters) -1)
            newpass = newpass + characters[index]

        self.new_password.set_text(newpass)
        self.confirm_password.set_text(newpass)
        self.check_passwords()

    def _on_show_password_toggled(self, widget):
        self.set_passwords_visibility()

    def _on_current_password_changed(self, widget, event):
        self.infobar.hide()
        if self.current_password.get_text() != "":
            auth = PAM.pam()
            auth.start('passwd')        
            auth.set_item(PAM.PAM_USER, GLib.get_user_name())
            auth.set_item(PAM.PAM_CONV, self.pam_conv)            
            try:
                auth.authenticate()
                auth.acct_mgmt()
            except PAM.error, resp:
                self.current_password.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_DIALOG_WARNING)
                self.current_password.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("Wrong password"))
                self.correct_current_password = False
            except:
                print 'Internal error'
            else:
                self.current_password.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, None)
                self.correct_current_password = True
                self.check_passwords()

    def _on_passwords_changed(self, widget):   
        self.infobar.hide() 
        new_password = self.new_password.get_text()
        confirm_password = self.confirm_password.get_text()
        if new_password != confirm_password:
            self.confirm_password.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, Gtk.STOCK_DIALOG_WARNING)
            self.confirm_password.set_icon_tooltip_text(Gtk.EntryIconPosition.SECONDARY, _("Passwords do not match"))
        else:
            self.confirm_password.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, None)
        if len(new_password) < 8:
            self.strengh_label.set_text(_("Too short"))
            self.strengh_indicator.set_fraction(0.0)
        else:
            self.strengh_label.set_text(_("OK"))
            self.strengh_indicator.set_fraction(1.0)

        self.check_passwords()

    def check_passwords(self):
        if self.correct_current_password:
            new_password = self.new_password.get_text()
            confirm_password = self.confirm_password.get_text()
            if len(new_password) >= 8 and new_password == confirm_password:
                self.set_response_sensitive(Gtk.ResponseType.OK, True)
            else:
                self.set_response_sensitive(Gtk.ResponseType.OK, False)

    def pam_conv(self, auth, query_list, userData):
        resp = []
        for i in range(len(query_list)):
            query, type = query_list[i]
            val = self.current_password.get_text()
            resp.append((val, 0))            
        return resp
