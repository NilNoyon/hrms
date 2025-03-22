from os import extsep
import os, re
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
from django.utils.text import Truncator
from io import BytesIO
from PIL import Image
from django.core.files import File
from general.templatetags import general_filters
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.contrib.contenttypes.models import ContentType
from general.forms import CommonLogForm
from general.models import CommonLogs

class Common:

    def form_errors(self, request, model_form):
        for field in model_form:
            for error in field.errors:
                messages.warning(request, "%s : %s" % (field.name, error))
                print('Form Error of ',"%s : %s" % (field.name, error))

    def form_error_print(self, request, model_form):
        for field in model_form:
            for error in field.errors:
                print("%s : %s" % (field.name, error))

    def ajax_form_errors(self, model_form):
        msg = ""
        for field in model_form:
            for error in field.errors:
                msg += "%s : %s" % (field.name, error)
                print(field.name, error)
        return msg
    
    def user_html(self, user, chars_value=20):
        if user : return '<a href="#aboutModal" data-toggle="modal" data-id="'+str(user.id)+'" class="user_info text-info" data-target="#userModal">'+Truncator(user.name).chars(chars_value)+'</a>'
        else : return ""
    def supplier_html(self, supplier, chars_value=20):
        return '<a href="#supplierModal" data-toggle="modal" data-id="'+str(supplier.id)+'" class="supplier_info text-info" data-target="#supplierModal">'+Truncator(supplier.name).chars(chars_value)+'</a>'

    def dept_short_name(self, dept):
        return (dept.short_name if dept.short_name else Truncator(dept.name).chars(20)) if dept else "N/A"

    def date_time_format(self, date_value, format='datetime'):
        if date_value   :
            if format == 'datetime' : value = date_value.strftime("%d-%b-%Y %I:%M %p")
            elif format == 'time'   : value = date_value.strftime("%I:%M %p")
            else                    : value = date_value.strftime("%d-%b-%Y")
            return str(value).upper()
        else            : return ''
    
    def datatable_center_td(self, value):
        return '<p class="text-center mb-0">' + str(value) + '</p>'

    def text_url(self, url, text, title_text=''):
        return '<a class="text-info" href="'+url+'" title="'+title_text+'" target="_blank">'+text+'</a>'
    
    def action_html(self, action_url, color_text="text-success", icon="icon-arrow-right-circle", icon_text='', title_text=''):
        action = '<a class="h4 m-r-10 '+color_text+'" href="'+action_url+'" title="'+title_text+'" target="_blank"><span class="icon">'
        if icon_text    : action += icon_text
        else            : action += '<i class="'+icon+'"></i>'
        action += '</span></a>'
        return action

    def show_pdf(self, request, pdf, filename):
        response                    = HttpResponse(pdf, content_type='application/pdf')
        content                     = "inline; filename="+filename 
        download                    = request.GET.get("download")
        if download: content        = "attachment; filename="+filename 
        response['Content-Disposition'] = content
        return response

    def compress(self, file):
        im_io   = BytesIO() 
        image   = Image.open(file)
        extension = (os.path.splitext(file.name)[1]).replace(".", "")
        image.save(image, extension, quality=20, optimize=True)
        return File(im_io, name=image.name)

    def retrun_str_from_xls(self, value):
        value = re.sub(' +', ' ', value)
        value = value.strip()
        value = inv_filters.strip_double_quotes(value)
        value = inv_filters.strip_single_quote(value)
        if str(value) == 'nan': value = ''
        else:
            if (isinstance(value, float)): value = int(value)
        return str(value)
        
    def download_excel_sheet(self, file_name):
        file_path = str(settings.MEDIA_ROOT)+'/excel_templates/'+ file_name
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
        raise Http404
    
    #Image Compress & save to directory
    def img_save_path(self,request,folder,input_name,file_name):
        try:
            if request.FILES[input_name].size < settings.DATA_UPLOAD_LIMIT:
                photo_path = "/"+folder+"/" + str(file_name)+".png"
                if not os.path.exists(str(settings.MEDIA_ROOT)+"/"+folder):
                    os.mkdir(str(settings.MEDIA_ROOT)+"/"+folder)

                if os.path.isfile(str(settings.MEDIA_ROOT)+photo_path):
                    os.remove(str(settings.MEDIA_ROOT)+photo_path)

                size = 200, 200 #photo saving dimension
                im = Image.open(request.FILES[input_name]).convert('RGB')
                im.thumbnail(size, Image.LANCZOS)
                
                im.save(str(settings.MEDIA_ROOT)+photo_path, format="PNG", quality=80)
                
                return photo_path
            else: return ""
        except Exception as e:
            messages.warning(request,str(e))
            return ""

    #File save to directory
    def file_save_path(self,request,folder,input_name,file_name):
        try:
            file = request.FILES[input_name]
            if file.size < settings.DATA_UPLOAD_LIMIT:
                file_extnsn = str(str(file).split(".")[1].lower())
                file_path = "/"+folder+"/" + str(file_name)+"."+file_extnsn
                if not os.path.exists(str(settings.MEDIA_ROOT)+"/"+folder):
                    os.mkdir(str(settings.MEDIA_ROOT)+"/"+folder)

                if os.path.isfile(str(settings.MEDIA_ROOT)+file_path):
                    os.remove(str(settings.MEDIA_ROOT)+file_path)

                default_storage.save(str(settings.MEDIA_ROOT) + file_path,ContentFile(file.read()))
                return file_path
            else: return ""
        except Exception as e:
            messages.warning(request,str(e))
            return ""

    #File save to directory in any size
    def max_file_save_path(self,request,folder,input_name,file_name):
        try:
            file = request.FILES[input_name]
            if file.size < settings.DATA_UPLOAD_MAX_LIMIT:
                file_extnsn = str(str(file).split(".")[1].lower())
                file_path = "/"+folder+"/" + str(file_name)+"."+file_extnsn
                if not os.path.exists(str(settings.MEDIA_ROOT)+"/"+folder):
                    os.mkdir(str(settings.MEDIA_ROOT)+"/"+folder)

                if os.path.isfile(str(settings.MEDIA_ROOT)+file_path):
                    os.remove(str(settings.MEDIA_ROOT)+file_path)

                default_storage.save(str(settings.MEDIA_ROOT) + file_path,ContentFile(file.read()))
                return file_path
            else: return ""
        except Exception as e:
            messages.warning(request,str(e))
            return ""

    # Update Nitification
    def update_notification(self, n_model='', n_verb='', n_receipent=''):
        from notification.models import Notification
        from django.utils import timezone
        notifyObj = Notification.objects.filter(model=n_model, verb__iexact=n_verb, unread=True, recipient=n_receipent).last()
        if notifyObj:
            d_text, delete_notification = [], False
            for text in notifyObj.description.split():
                if text.isdigit():
                    text = int(text) - 1
                    d_text.append(str(text))
                    if text == 0 : delete_notification = True
                else : d_text.append(text)
            des_text = " ".join(d_text)
            if delete_notification : notifyObj.delete()
            else :
                notifyObj.description   = des_text
                notifyObj.timestamp     = timezone.now()
                notifyObj.save()

    def is_ajax(self, request) :
        return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

    def textile_wastage(self, value, wastage):
        if value:
            value_with_wastage = round((float(value)/float(((100-float(wastage))/100))),6) #Consumption With Wastage = consumption/((100-wastage)/100)
            wastage = float(value_with_wastage) - float(value)
            return value_with_wastage, wastage
        else: return 0, wastage
    
    def send_email(self, subject, message, recipients): # recipients will be the list [recipients] = ["email1","email2"]
        try:
            from ngohrms import settings
            if settings.TEST_EMAIL: recipients = [str(settings.TEST_EMAIL)]
            mail = EmailMessage(subject, message , settings.EMAIL_HOST_USER, recipients)
            mail.content_subtype = "html"
            # if settings.DOMAIN_URL == '':
            #     mail.send()
        except: pass
    
    def mssql_db_connect(self): #For Connection
        try:
            from ngohrms import settings
            import pymssql
            conn = pymssql.connect(
                host = settings.MS_SERVER, 
                port = settings.MS_DB_PORT, 
                user = settings.MS_DB_USER,
                password = settings.MS_DB_PASS,
                database = settings.MS_DB_NAME
            )
            cursor = conn.cursor(as_dict=True)
            return cursor
        except: return None
        
    def mssql_query(self, query): #For getting data from server
        try:
            connection, data = self.mssql_db_connect(), None
            if connection:
                print('Connected!')
                connection.execute(query)
                data = connection.fetchall()
                connection.close()
            else : print('Failed!')
            return data
        except : return None
        
        
    def common_log_entry(self, instance, previous_status, status, description, ip_address, log_by = None):
        try:
            msg, icon = "", "success"
            form_data = {}
            form_data["content_type"] = ContentType.objects.get_for_model(instance)
            form_data["object_id"]    = instance.id
            form_data["previous_status"] = previous_status
            form_data["status"]       = status
            form_data["description"]  = description
            form_data["ip_address"]   = ip_address
            form_data["log_by"]       = log_by
        
            form = CommonLogForm(form_data)
            if form.is_valid():
                form.save()
                msg = "Log Entry Successful"
            else: 
                msg  = self.ajax_form_errors(form)    
                icon = "warning"     
            return msg, icon
        except:pass
    
    def common_log_history(self, instance):
        try:
            ContentType.objects.get_for_model(instance)
            data_list = list(CommonLogs.objects.filter(content_type = ContentType.objects.get_for_model(instance), object_id = str(instance.id)).order_by("-id"))
            return data_list
        except:pass

    def getIP(self):
        user_ip, server_ip, mac_address, mac_address2 = None, None, None, None
        try :
            import requests, socket
            from getmac import get_mac_address
            server_ip   = socket.gethostbyname(socket.gethostname())
            user_ip     = requests.get("https://www.wikipedia.org").headers["X-Client-IP"]
            mac_address = get_mac_address(ip=server_ip) if server_ip else None
        except : pass
        return server_ip, user_ip, mac_address

    def create_custom_session(self, user, request):
        from django.utils import timezone
        from general.models import CustomSession
        server_ip, user_ip, mac_address = self.getIP()
        CustomSession.objects.create(user=user, local_ip_address=user_ip, ip_address=server_ip, 
            mac_address=mac_address, created_at=timezone.now())
        