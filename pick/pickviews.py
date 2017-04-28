# coding: utf-8
from depot.models import Pick, PickItem
from shipping.models import Package,PackageItem, ItemLocked
from lib.utils import pp


def group_by_depotitem(package_ids):
    """将package中的产品, 根据depot_item进行分组, 并将分组好的数据根据库位进行排序"""
    item_lockeds = ItemLocked.objects.filter(package_item__package_id__in=package_ids)\
                                     .values_list('depot_item_id', 'depot_item__position', 
                                                  'package_item__package_id', 'qty', 'depot_item__item__sku',
                                                  'depot_item__item__product__category__cn_name')
    # 根据depot_item进行分组
    depot_items = {}
    for depot_item_id, position, package_id, qty, sku, cn_name in item_lockeds:                                     
        if depot_item_id not in depot_items:
            depot_items[depot_item_id] = {
                'depot_item_id': depot_item_id,
                'qty': qty,
                'package_ids': {package_id:qty, },
                'position': position,
                'sku': sku,
                'cn_name': cn_name,
            }
        else:
            depot_items[depot_item_id]['qty'] += qty
            depot_items[depot_item_id]['package_ids'][package_id] = qty

    items = [value for depot_item_id, value in depot_items.iteritems()]

    # 把产品根据position进行排序
    items.sort(key=lambda x:x['position'])
    return items

# 单单和单多
def create_single_sku_pick(package_ids, depot, shipping, pick_type, user):
    """单单和单多都可以使用这个方法"""
    # 获取package中产品, 并分组, 排序
    items = group_by_depotitem(package_ids)

    # 每次取20个items, 用于生成pick单
    per_page = 20
    pick_nums = 0
    for sub_items in [items[i:i+per_page] for i in xrange(0, len(items), per_page)]:
        # 生成pick单
        pick = Pick.objects.create(code=depot, shipping=shipping, pick_type=pick_type, user_adder=user)

        # 更新这些产品对应package的pick, 同时生成对应的packageitem
        all_package_ids = []
        for sub_item in sub_items:
            PickItem.objects.create(pick=pick, depot_item_id=sub_item['depot_item_id'], qty=sub_item['qty'])

            all_package_ids.extend(sub_item['package_ids'].keys())

        Package.objects.filter(id__in=all_package_ids).update(pick_id=pick.id)

        pick_nums += 1

    return pick_nums


# 多多
def create_multi_sku_pick(package_ids, depot, shipping, pick_type, user):
    """多多packages根据库位得分进行排序, 每个pick表捡20个package"""
    #
    packages = list(Package.objects.filter(id__in=package_ids).values_list('id', 'position_score'))
    packages.sort(key=lambda x:x[1])

    per_page = 20
    pick_nums = 0
    for sub_packages in [packages[i:i+per_page] for i in xrange(0, len(packages), per_page)]:
        # 生成pick单
        pick = Pick.objects.create(code=depot, shipping=shipping, pick_type=pick_type, user_adder=user)

        sub_pids = [i[0] for i in sub_packages]
        Package.objects.filter(id__in=sub_pids).update(pick_id=pick.id)

        # 获取package中产品, 并分组, 排序, 从而创建pickitem
        items = group_by_depotitem(sub_pids)
        for sub_item in items:
            PickItem.objects.create(pick=pick, depot_item_id=sub_item['depot_item_id'], qty=sub_item['qty'])

        pick_nums += 1

    return pick_nums


def get_pick_html_data(pick_id):
    """获取拣货用html的数据"""
    package_ids = Package.objects.filter(pick_id=pick_id).values_list('id', flat=True)
    items = group_by_depotitem(list(package_ids))
    return items




