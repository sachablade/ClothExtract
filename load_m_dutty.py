# coding=utf-8
import json, requests
import traceback

import sys

import os

__HEADERS__ = ['subFamilyName', 'id', 'Reference', 'name', 'ColorName', 'idColor','inStock', 'initialPrice', 'discountPrice',
               'composition']


def get_new_proxy2():
    resp = requests.get(url='https://api.getproxylist.com/proxy')
    data_proxy = json.loads(resp.text)
    return {'http': 'http://%s:%d' % (data_proxy['ip'].encode(), data_proxy['port']),
            'https': 'https://%s:%d' % (data_proxy['ip'].encode(), data_proxy['port'])}


def get_new_proxy():
    resp = requests.get(url='http://pubproxy.com/api/proxy', proxies={'http': 'http://149.255.154.4:8080'})
    data_proxy = json.loads(resp.text)
    return {'http': 'http://%s' % (data_proxy['data'][0]['ipPort'].encode()),
            'https': 'https://%s' % (data_proxy['data'][0]['ipPort'].encode())}


def is_in_stock(data_stock, colors, id=None):
    availibility_list = []
    try:
        sku_list = [[color['name'],[sku['sku'] for sku in color['sizes']]] for color in colors]
        for p in data_stock['stocks']:
            for elements in p['stocks']:
                for sku in sku_list:
                    if elements['id'] in sku[1]:
                        if elements['availability'] == 'in_stock':
                            availibility_list.append(sku[0])

        return list(set(availibility_list))
    except Exception as e:
        print e


def get_cloth(url_simplificado, id):
    url = url_simplificado + '%s/product?languageId=-5&appId=1' % id
    resp = requests.get(url=url)
    data = json.loads(resp.text)

    url = url_simplificado + '%s/stock?withSubCategories=false&languageId=-5&appId=1' % id
    resp = requests.get(url=url)
    data_stock = json.loads(resp.text)

    proxy = get_new_proxy()
    for product in data['products']:
        try:
            obj = [''] * 10
            if len(product['bundleProductSummaries']) > 0:
                try:
                    obj[__HEADERS__.index('subFamilyName')] = product['bundleProductSummaries'][0]['subFamilyName']

                except Exception as e:
                    pass

                obj[__HEADERS__.index('id')] = product['bundleProductSummaries'][0]['id']
                detail_url = "%s0/product/%s/detail?languageId=-5&appId=1" % (
                url_simplificado, obj[__HEADERS__.index('id')])

                if not os.path.isfile('state/%s.json' % obj[__HEADERS__.index('id')]):
                    while True:
                        try:
                            resp = requests.get(url=detail_url, proxies=proxy)
                            data_detail = json.loads(resp.text)
                            with open('state/%s.json' % obj[__HEADERS__.index('id')], 'w') as fp:
                                json.dump(data_detail, fp)
                            break
                        except Exception as e:
                            print('nooooo')
                            proxy = get_new_proxy()
                else:
                    data_detail = json.loads(open('state/%s.json' % obj[__HEADERS__.index('id')], "r").read())

                try:
                    composition = data_detail['detail']['composition']
                    obj[__HEADERS__.index('composition')] = ';'.join(
                        [i['composition'][0]['percentage'] + '% ' + i['composition'][0]['name'] for i in composition])
                except Exception as e:
                    pass

                obj[__HEADERS__.index('Reference')] = product['bundleProductSummaries'][0]['detail']['displayReference']
                obj[__HEADERS__.index('name')] = product['bundleProductSummaries'][0]['name']

                if len(product['bundleProductSummaries'][0]['detail']['colors']) == 1:
                    in_stock = is_in_stock(data_stock, product['bundleProductSummaries'][0]['detail']['colors'],
                                obj[__HEADERS__.index('id')])
                    colors = product['bundleProductSummaries'][0]['detail']['colors'][0]

                    obj[__HEADERS__.index('ColorName')] = colors['name']
                    obj[__HEADERS__.index('idColor')] = colors['id']

                    obj[__HEADERS__.index('inStock')] = False
                    if obj[__HEADERS__.index('ColorName')] in in_stock:
                        obj[__HEADERS__.index('inStock')] = True

                    if len(product['bundleProductSummaries'][0]['detail']['colors'][0]['sizes']) > 0:
                        sizes = product['bundleProductSummaries'][0]['detail']['colors'][0]['sizes'][0]
                        obj[__HEADERS__.index('initialPrice')] = float(sizes['price']) / 100
                        if sizes['oldPrice'] is not None:
                            obj[__HEADERS__.index('discountPrice')] = float(colors['sizes'][0]['oldPrice']) / 100

                        if obj[__HEADERS__.index('discountPrice')] <> '':
                            if obj[__HEADERS__.index('initialPrice')] < obj[__HEADERS__.index('discountPrice')]:
                                init_price = obj[__HEADERS__.index('discountPrice')]
                                obj[__HEADERS__.index('discountPrice')] = obj[__HEADERS__.index('initialPrice')]
                                obj[__HEADERS__.index('initialPrice')] = init_price

                        yield obj

                else:
                    in_stock = is_in_stock(data_stock, product['bundleProductSummaries'][0]['detail']['colors'])
                    for colors in product['bundleProductSummaries'][0]['detail']['colors']:
                        obj = list(obj)
                        obj[__HEADERS__.index('ColorName')] = colors['name']
                        obj[__HEADERS__.index('idColor')] = colors['id']


                        obj[__HEADERS__.index('inStock')] = False
                        if obj[__HEADERS__.index('ColorName')] in in_stock:
                            obj[__HEADERS__.index('inStock')] = True

                        if len(colors['sizes']) > 0:

                            obj[__HEADERS__.index('initialPrice')] = float(colors['sizes'][0]['price']) / 100
                            if colors['sizes'][0]['oldPrice'] is not None:
                                obj[__HEADERS__.index('discountPrice')] = float(colors['sizes'][0]['oldPrice']) / 100

                            if obj[__HEADERS__.index('discountPrice')] <> '':
                                if obj[__HEADERS__.index('initialPrice')] < obj[__HEADERS__.index('discountPrice')]:
                                    init_price = obj[__HEADERS__.index('discountPrice')]
                                    obj[__HEADERS__.index('discountPrice')] = obj[__HEADERS__.index('initialPrice')]
                                    obj[__HEADERS__.index('initialPrice')] = init_price

                        yield list(obj)

        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            raise e


if __name__ == '__main__':
    url_camisetas = 'https://www.massimodutti.com/itxrest/2/catalog/store/34009450/30359464/category/'
    camisetas = [i for i in get_cloth(url_camisetas, '911194')]
    url_camisetas = 'https://www.massimodutti.com/itxrest/2/catalog/store/34009450/30359464/category/'
    jerseys = [i for i in get_cloth(url_camisetas, '911188')]

    camisetas.extend(jerseys)
    import pandas as pd

    df = pd.DataFrame(camisetas, columns=__HEADERS__)
    df.to_excel('3report.xlsx')
