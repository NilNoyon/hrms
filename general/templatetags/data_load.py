from django.db.models import Count
from django import template
from general.models import UserPermission, MenuList
from django.db.models import Q
from django.core.cache import cache

register = template.Library()

@register.filter(name='menu_list')
def menu_load(employee_id):
    # menus = cache.get('my_menulist')
    # if menus: return menus
    
    menu_counts = UserPermission.objects.filter((Q(view_action = True)|Q(insert_action = True)|Q(update_action = True)|Q(delete_action = True))
        ,user_id = employee_id, menu__status = True).values("menu__module_name").annotate(total_count=Count('menu__module_name')
        ).order_by("-total_count")
    menus = []
    for m in menu_counts:
        menu = UserPermission.objects.filter((Q(view_action = True)|Q(insert_action = True)|Q(update_action = True)|Q(delete_action = True))
            ,user_id = employee_id, menu__status = True, menu__module_name=m['menu__module_name']).order_by(
            "menu__module_name","menu__is_sub_menu", "menu__menu_order", "menu__sub_menu_name").values(
            "menu__module_name","menu__menu_icon", "menu__menu_icon", "menu__menu_url", "menu__menu_name", 
            "menu__is_sub_menu", "menu__menu_order", "menu__sub_menu_name")
        menus += list(menu)
    # cache.add('my_menulist', menus, 600)
    return menus if menus else None

# @register.filter(name='menu_list')
# def menu_load(employee_id, module_name):
#     menus = HrUserAccessControl.objects.filter(employee_id = employee_id, menu_id__module_name = module_name, menu_id__status = True).order_by("menu_id__menu_order")
#     if menus: return menus    
#     else: return None

@register.filter(name='others_module_list')
def others_module_load(employee_id):
    menu_counts = UserPermission.objects.filter((Q(view_action = True)|Q(insert_action = True)|Q(update_action = True)|Q(delete_action = True))
        ,user_id = employee_id, menu__status = True).values("menu__module_name").annotate(total_count=Count('menu__module_name')
        ).order_by("-total_count")[3:]
    menus = []
    for m in menu_counts:
        menu = UserPermission.objects.filter((Q(view_action = True)|Q(insert_action = True)|Q(update_action = True)|Q(delete_action = True))
            ,user_id = employee_id, menu__status = True, menu__module_name=m['menu__module_name']).order_by(
            "menu__module_name","menu__is_sub_menu", "menu__menu_order", "menu__sub_menu_name").values(
            "menu__module_name","menu__menu_icon", "menu__menu_icon", "menu__menu_url", "menu__menu_name", 
            "menu__is_sub_menu", "menu__menu_order", "menu__sub_menu_name", "menu_id")
        menus += list(menu)
    return menus if menus else None
    # # sub_query = list(UserPermission.objects.values_list("menu__module_name",flat = True).filter(user_id = employee_id, menu__status = True).distinct("menu__module_name"))
    # sub_query = UserPermission.objects.filter((Q(view_action = True)|Q(insert_action = True)|Q(update_action = True)|Q(delete_action = True)),user_id = employee_id, menu__status = True).order_by("menu__module_name","menu__is_sub_menu", "menu__menu_order", "menu__sub_menu_name")
    # if sub_query: return sub_query    
    # else: return None

    # module_list = list(map(lambda x: x[0], MenuList.module_types))
    # for i in sub_query:
    #     module_list.remove(i)
    # if module_list: return module_list    
    # else: return None
    
@register.filter(name='unpermitted_menu_list')
def unpermitted_menu_load(obj, user_id): #this will be the permitted menu list under a module with sub module if have
    related_menu = obj[0]
    related_menus = MenuList.objects.filter(module_name = related_menu["menu__module_name"], is_sub_menu = related_menu["menu__is_sub_menu"], sub_menu_name = related_menu["menu__sub_menu_name"]).exclude(userpermission__user_id = int(user_id))
    return related_menus
    
@register.simple_tag
def variable_assign(val=None):
    return val

@register.filter(name='is_role_assigned')
def is_role_assigned(roles=[], roles_checking='') :
    roles = [rl.lower() for rl in roles]
    if type(roles_checking) not in (tuple, list) : roles_checking = roles_checking.split(",")
    roles_checking = [rl.lower() for rl in roles_checking]
    return (True if any(role.strip() in roles for role in roles_checking) else False) if roles else False

@register.filter(name='notice_list')
def notice_list(employee_id):
    from general.models import Status
    from hr.models import NoticeBoard
    from datetime import datetime
    current_time = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
    all_notices = NoticeBoard.objects.filter(start_date__lte=current_time, end_date__gte=current_time, status=Status.name("active"))
    return all_notices

@register.filter(name='check_process')
def check_process(condition_process, process):
    if type(condition_process) not in (tuple, list) : condition_process = condition_process.split(",")
    return any(True for i in process if i in condition_process)