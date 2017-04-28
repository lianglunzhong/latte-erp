#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Basic interface to Amazon MWS
# Based on http://code.google.com/p/amazon-mws-python
#

import urllib
import hashlib
import hmac
import base64
import re
from xml.etree import cElementTree as ET
from collections import defaultdict

try:
    from xml.etree.ElementTree import ParseError as XMLError
except ImportError:
    from xml.parsers.expat import ExpatError as XMLError
from time import strftime, gmtime

from requests import request
from requests.exceptions import HTTPError

def etree_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.iteritems():
                dd[k].append(v)
        #d = {t.tag: {k:v[0] if len(v) == 1 else v for k, v in dd.iteritems()}}
        ddd = {}
        for k, v in dd.iteritems():
            if len(v) == 1:
                ddd[k] = v[0]
            else:
                ddd[k] = v
        d = {t.tag:ddd }
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.iteritems())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


__all__ = [
    'Feeds',
    'Inventory',
    'MWSError',
    'Reports',
    'Orders',
    'Products',
    'Recommendations',
    'Sellers',
]

# See https://images-na.ssl-images-amazon.com/images/G/01/mwsportal/doc/en_US/bde/MWSDeveloperGuide._V357736853_.pdf page 8
# for a list of the end points and marketplace IDs

MARKETPLACES = {
    "CA" : "https://mws.amazonservices.ca", #A2EUQ1WTGCTBG2
    "US" : "https://mws.amazonservices.com", #ATVPDKIKX0DER",
    "DE" : "https://mws-eu.amazonservices.com", #A1PA6795UKMFR9
    "ES" : "https://mws-eu.amazonservices.com", #A1RKKUPIHCS9HS
    "FR" : "https://mws-eu.amazonservices.com", #A13V1IB3VIYZZH
    "IN" : "https://mws.amazonservices.in", #A21TJRUUN4KGV
    "IT" : "https://mws-eu.amazonservices.com", #APJ6JRA9NG5V4
    "UK" : "https://mws-eu.amazonservices.com", #A1F83G8C2ARO7P
    "JP" : "https://mws.amazonservices.jp", #A1VC38T7YXB528
    "CN" : "https://mws.amazonservices.com.cn", #AAHKV2X7AFYLW
    "MX" : "https://mws.amazonservices.com.mx", #A1AM78C64UM0Y8    
}


class MWSError(Exception):
    """
        Main MWS Exception class
    """
    # Allows quick access to the response object.
    # Do not rely on this attribute, always check if its not None.
    response = None


def calc_md5(string):
    """Calculates the MD5 encryption for the given string
    """
    md = hashlib.md5()
    md.update(string)
    return base64.encodestring(md.digest()).strip('\n')


def remove_empty(d):
    """
        Helper function that removes all keys from a dictionary (d),
        that have an empty value.
    """
    for key in d.keys():
        if not d[key]:
            del d[key]
    return d


def remove_namespace(xml):
    regex = re.compile(' xmlns(:ns2)?="[^"]+"|(ns2:)|(xml:)')
    return regex.sub('', xml)


class DictWrapper(object):
    def __init__(self, xml, rootkey=None):
        self.original = xml
        self._rootkey = rootkey

        e = ET.XML(remove_namespace(xml))
        self._mydict = etree_to_dict(e)
        #self._mydict = utils.xml2dict().fromstring(remove_namespace(xml))
        self._response_dict = self._mydict.get(self._mydict.keys()[0],
                                               self._mydict)

    @property
    def parsed(self):
        if self._rootkey:
            return self._response_dict.get(self._rootkey)
        else:
            return self._response_dict



class DataWrapper(object):
    """
        Text wrapper in charge of validating the hash sent by Amazon.
    """
    def __init__(self, data, header):
        self.original = data
        if 'content-md5' in header:
            hash_ = calc_md5(self.original)
            if header['content-md5'] != hash_:
                raise MWSError("Wrong Contentlength, maybe amazon error...")

    @property
    def parsed(self):
        return self.original


class MWS(object):
    """ Base Amazon API class """

    # This is used to post/get to the different uris used by amazon per api
    # ie. /Orders/2011-01-01
    # All subclasses must define their own URI only if needed
    URI = "/"

    # The API version varies in most amazon APIs
    VERSION = "2009-01-01"

    # There seem to be some xml namespace issues. therefore every api subclass
    # is recommended to define its namespace, so that it can be referenced
    # like so AmazonAPISubclass.NS.
    # For more information see http://stackoverflow.com/a/8719461/389453
    NS = ''

    # Some APIs are available only to either a "Merchant" or "Seller"
    # the type of account needs to be sent in every call to the amazon MWS.
    # This constant defines the exact name of the parameter Amazon expects
    # for the specific API being used.
    # All subclasses need to define this if they require another account type
    # like "Merchant" in which case you define it like so.
    # ACCOUNT_TYPE = "Merchant"
    # Which is the name of the parameter for that specific account type.
    ACCOUNT_TYPE = "SellerId"

    def __init__(self, access_key, secret_key, account_id, region='US', domain='', uri="", version="", auth_token=""):
        self.access_key = access_key
        self.secret_key = secret_key
        self.account_id = account_id
        self.auth_token = auth_token
        self.version = version or self.VERSION
        self.uri = uri or self.URI

        if domain:
            self.domain = domain
        elif region in MARKETPLACES:
            self.domain = MARKETPLACES[region]
        else:
            error_msg = "Incorrect region supplied ('%(region)s'). Must be one of the following: %(marketplaces)s" % {
                "marketplaces" : ', '.join(MARKETPLACES.keys()),
                "region" : region,
            }
            raise MWSError(error_msg)

    def make_request(self, extra_data, method="GET", **kwargs):
        """Make request to Amazon MWS API with these parameters
        """

        # Remove all keys with an empty value because
        # Amazon's MWS does not allow such a thing.
        extra_data = remove_empty(extra_data)

        params = {
            'AWSAccessKeyId': self.access_key,
            self.ACCOUNT_TYPE: self.account_id,
            'SignatureVersion': '2',
            'Timestamp': self.get_timestamp(),
            'Version': self.version,
            'SignatureMethod': 'HmacSHA256',
        }
        if self.auth_token:
            params['MWSAuthToken'] = self.auth_token
        params.update(extra_data)
        request_description = '&'.join(['%s=%s' % (k, urllib.quote(params[k], safe='-_.~').encode('utf-8')) for k in sorted(params)])
        signature = self.calc_signature(method, request_description)
        url = '%s%s?%s&Signature=%s' % (self.domain, self.uri, request_description, urllib.quote(signature))
        headers = {'User-Agent': 'python-amazon-mws/0.0.1 (Language=Python)'}
        headers.update(kwargs.get('extra_headers', {}))

        try:
            # Some might wonder as to why i don't pass the params dict as the params argument to request.
            # My answer is, here i have to get the url parsed string of params in order to sign it, so
            # if i pass the params dict as params to request, request will repeat that step because it will need
            # to convert the dict to a url parsed string, so why do it twice if i can just pass the full url :).
            response = request(method, url, data=kwargs.get('body', ''), headers=headers)
            response.raise_for_status()
            # When retrieving data from the response object,
            # be aware that response.content returns the content in bytes while response.text calls
            # response.content and converts it to unicode.
            data = response.content

            # I do not check the headers to decide which content structure to server simply because sometimes
            # Amazon's MWS API returns XML error responses with "text/plain" as the Content-Type.
            try:
                parsed_response = DictWrapper(data, extra_data.get("Action") + "Result")
            except XMLError:
                parsed_response = DataWrapper(data, response.headers)

        except HTTPError, e:
            error = MWSError(str(e.response.text))
            error.response = e.response
            raise error

        # Store the response object in the parsed_response for quick access
        parsed_response.response = response
        return parsed_response

    def get_service_status(self):
        """
            Returns a GREEN, GREEN_I, YELLOW or RED status.
            Depending on the status/availability of the API its being called from.
        """

        return self.make_request(extra_data=dict(Action='GetServiceStatus'))

    def calc_signature(self, method, request_description):
        """Calculate MWS signature to interface with Amazon
        """
        sig_data = method + '\n' + self.domain.replace('https://', '').lower() + '\n' + self.uri + '\n' + request_description
        return base64.b64encode(hmac.new(str(self.secret_key), sig_data, hashlib.sha256).digest())

    def get_timestamp(self):
        """
            Returns the current timestamp in proper format.
        """
        return strftime("%Y-%m-%dT%H:%M:%SZ", gmtime())

    def enumerate_param(self, param, values):
        """
            Builds a dictionary of an enumerated parameter.
            Takes any iterable and returns a dictionary.
            ie.
            enumerate_param('MarketplaceIdList.Id', (123, 345, 4343))
            returns
            {
                MarketplaceIdList.Id.1: 123,
                MarketplaceIdList.Id.2: 345,
                MarketplaceIdList.Id.3: 4343
            }
        """
        params = {}
        if values is not None:
            if not param.endswith('.'):
                param = "%s." % param
            for num, value in enumerate(values):
                params['%s%d' % (param, (num + 1))] = value
        return params


class Feeds(MWS):
    """ Amazon MWS Feeds API """

    ACCOUNT_TYPE = "Merchant"

    def submit_feed(self, feed, feed_type, marketplaceids=None,
                    content_type="text/xml", purge='false'):
        """
        Uploads a feed ( xml or .tsv ) to the seller's inventory.
        Can be used for creating/updating products on Amazon.
        """
        data = dict(Action='SubmitFeed',
                    FeedType=feed_type,
                    PurgeAndReplace=purge)
        data.update(self.enumerate_param('MarketplaceIdList.Id.', marketplaceids))
        md = calc_md5(feed)
        return self.make_request(data, method="POST", body=feed,
                                 extra_headers={'Content-MD5': md, 'Content-Type': content_type})

    def get_feed_submission_list(self, feedids=None, max_count=None, feedtypes=None,
                                    processingstatuses=None, fromdate=None, todate=None):
        """
        Returns a list of all feed submissions submitted in the previous 90 days.
        That match the query parameters.
        """

        data = dict(Action='GetFeedSubmissionList',
                    MaxCount=max_count,
                    SubmittedFromDate=fromdate,
                    SubmittedToDate=todate,)
        data.update(self.enumerate_param('FeedSubmissionIdList.Id', feedids))
        data.update(self.enumerate_param('FeedTypeList.Type.', feedtypes))
        data.update(self.enumerate_param('FeedProcessingStatusList.Status.', processingstatuses))
        return self.make_request(data)

    def get_submission_list_by_next_token(self, token):
        data = dict(Action='GetFeedSubmissionListByNextToken', NextToken=token)
        return self.make_request(data)

    def get_feed_submission_count(self, feedtypes=None, processingstatuses=None, fromdate=None, todate=None):
        data = dict(Action='GetFeedSubmissionCount',
                    SubmittedFromDate=fromdate,
                    SubmittedToDate=todate)
        data.update(self.enumerate_param('FeedTypeList.Type.', feedtypes))
        data.update(self.enumerate_param('FeedProcessingStatusList.Status.', processingstatuses))
        return self.make_request(data)

    def cancel_feed_submissions(self, feedids=None, feedtypes=None, fromdate=None, todate=None):
        data = dict(Action='CancelFeedSubmissions',
                    SubmittedFromDate=fromdate,
                    SubmittedToDate=todate)
        data.update(self.enumerate_param('FeedSubmissionIdList.Id.', feedids))
        data.update(self.enumerate_param('FeedTypeList.Type.', feedtypes))
        return self.make_request(data)

    def get_feed_submission_result(self, feedid):
        data = dict(Action='GetFeedSubmissionResult', FeedSubmissionId=feedid)
        return self.make_request(data)


class Reports(MWS):
    """ Amazon MWS Reports API """

    ACCOUNT_TYPE = "Merchant"

    ## REPORTS ###

    def get_report(self, report_id):
        data = dict(Action='GetReport', ReportId=report_id)
        return self.make_request(data)

    def get_report_count(self, report_types=(), acknowledged=None, fromdate=None, todate=None):
        data = dict(Action='GetReportCount',
                    Acknowledged=acknowledged,
                    AvailableFromDate=fromdate,
                    AvailableToDate=todate)
        data.update(self.enumerate_param('ReportTypeList.Type.', report_types))
        return self.make_request(data)

    def get_report_list(self, requestids=(), max_count=None, types=(), acknowledged=None,
                        fromdate=None, todate=None):
        data = dict(Action='GetReportList',
                    Acknowledged=acknowledged,
                    AvailableFromDate=fromdate,
                    AvailableToDate=todate,
                    MaxCount=max_count)
        data.update(self.enumerate_param('ReportRequestIdList.Id.', requestids))
        data.update(self.enumerate_param('ReportTypeList.Type.', types))
        return self.make_request(data)

    def get_report_list_by_next_token(self, token):
        data = dict(Action='GetReportListByNextToken', NextToken=token)
        return self.make_request(data)

    def get_report_request_count(self, report_types=(), processingstatuses=(), fromdate=None, todate=None):
        data = dict(Action='GetReportRequestCount',
                    RequestedFromDate=fromdate,
                    RequestedToDate=todate)
        data.update(self.enumerate_param('ReportTypeList.Type.', report_types))
        data.update(self.enumerate_param('ReportProcessingStatusList.Status.', processingstatuses))
        return self.make_request(data)

    def get_report_request_list(self, requestids=(), types=(), processingstatuses=(),
                                max_count=None, fromdate=None, todate=None):
        data = dict(Action='GetReportRequestList',
                    MaxCount=max_count,
                    RequestedFromDate=fromdate,
                    RequestedToDate=todate)
        data.update(self.enumerate_param('ReportRequestIdList.Id.', requestids))
        data.update(self.enumerate_param('ReportTypeList.Type.', types))
        data.update(self.enumerate_param('ReportProcessingStatusList.Status.', processingstatuses))
        return self.make_request(data)

    def get_report_request_list_by_next_token(self, token):
        data = dict(Action='GetReportRequestListByNextToken', NextToken=token)
        return self.make_request(data)

    def request_report(self, report_type, start_date=None, end_date=None, marketplaceids=()):
        data = dict(Action='RequestReport',
                    ReportType=report_type,
                    StartDate=start_date,
                    EndDate=end_date)
        data.update(self.enumerate_param('MarketplaceIdList.Id.', marketplaceids))
        return self.make_request(data)


    ### ReportSchedule ###

    def get_report_schedule_list(self, types=()):
        data = dict(Action='GetReportScheduleList')
        data.update(self.enumerate_param('ReportTypeList.Type.', types))
        return self.make_request(data)

    def get_report_schedule_count(self, types=()):
        data = dict(Action='GetReportScheduleCount')
        data.update(self.enumerate_param('ReportTypeList.Type.', types))
        return self.make_request(data)


class Orders(MWS):
    """ Amazon Orders API """

    URI = "/Orders/2011-01-01"
    VERSION = "2011-01-01"
    NS = '{https://mws.amazonservices.com/Orders/2011-01-01}'

    URI = "/Orders/2013-09-01"
    VERSION = "2013-09-01"
    NS = '{https://mws.amazonservices.com/Orders/2011-09-01}'

    def list_orders(self, marketplaceids, created_after=None, created_before=None, lastupdatedafter=None,
                    lastupdatedbefore=None, orderstatus=(), fulfillment_channels=(),
                    payment_methods=(), buyer_email=None, seller_orderid=None, max_results='100'):

        data = dict(Action='ListOrders',
                    CreatedAfter=created_after,
                    CreatedBefore=created_before,
                    LastUpdatedAfter=lastupdatedafter,
                    LastUpdatedBefore=lastupdatedbefore,
                    BuyerEmail=buyer_email,
                    SellerOrderId=seller_orderid,
                    MaxResultsPerPage=max_results,
                    )
        data.update(self.enumerate_param('OrderStatus.Status.', orderstatus))
        data.update(self.enumerate_param('MarketplaceId.Id.', marketplaceids))
        data.update(self.enumerate_param('FulfillmentChannel.Channel.', fulfillment_channels))
        data.update(self.enumerate_param('PaymentMethod.Method.', payment_methods))
        return self.make_request(data)

    def list_orders_by_next_token(self, token):
        data = dict(Action='ListOrdersByNextToken', NextToken=token)
        return self.make_request(data)

    def get_order(self, amazon_order_ids):
        data = dict(Action='GetOrder')
        data.update(self.enumerate_param('AmazonOrderId.Id.', amazon_order_ids))
        return self.make_request(data)

    def list_order_items(self, amazon_order_id):
        data = dict(Action='ListOrderItems', AmazonOrderId=amazon_order_id)
        return self.make_request(data)

    def list_order_items_by_next_token(self, token):
        data = dict(Action='ListOrderItemsByNextToken', NextToken=token)
        return self.make_request(data)


class Products(MWS):
    """ Amazon MWS Products API """

    URI = '/Products/2011-10-01'
    VERSION = '2011-10-01'
    NS = '{http://mws.amazonservices.com/schema/Products/2011-10-01}'

    def list_matching_products(self, marketplaceid, query, contextid=None):
        """ Returns a list of products and their attributes, ordered by
            relevancy, based on a search query that you specify.
            Your search query can be a phrase that describes the product
            or it can be a product identifier such as a UPC, EAN, ISBN, or JAN.
        """
        data = dict(Action='ListMatchingProducts',
                    MarketplaceId=marketplaceid,
                    Query=query,
                    QueryContextId=contextid)
        return self.make_request(data)

    def get_matching_product(self, marketplaceid, asins):
        """ Returns a list of products and their attributes, based on a list of
            ASIN values that you specify.
        """
        data = dict(Action='GetMatchingProduct', MarketplaceId=marketplaceid)
        data.update(self.enumerate_param('ASINList.ASIN.', asins))
        return self.make_request(data)

    def get_matching_product_for_id(self, marketplaceid, type, ids):
        """ Returns a list of products and their attributes, based on a list of
            product identifier values (ASIN, SellerSKU, UPC, EAN, ISBN, GCID  and JAN)
            The identifier type is case sensitive.
            Added in Fourth Release, API version 2011-10-01
        """
        data = dict(Action='GetMatchingProductForId',
                    MarketplaceId=marketplaceid,
                    IdType=type)
        data.update(self.enumerate_param('IdList.Id.', ids))
        return self.make_request(data)

    def get_competitive_pricing_for_sku(self, marketplaceid, skus):
        """ Returns the current competitive pricing of a product,
            based on the SellerSKU and MarketplaceId that you specify.
        """
        data = dict(Action='GetCompetitivePricingForSKU', MarketplaceId=marketplaceid)
        data.update(self.enumerate_param('SellerSKUList.SellerSKU.', skus))
        return self.make_request(data)

    def get_competitive_pricing_for_asin(self, marketplaceid, asins):
        """ Returns the current competitive pricing of a product,
            based on the ASIN and MarketplaceId that you specify.
        """
        data = dict(Action='GetCompetitivePricingForASIN', MarketplaceId=marketplaceid)
        data.update(self.enumerate_param('ASINList.ASIN.', asins))
        return self.make_request(data)

    def get_lowest_offer_listings_for_sku(self, marketplaceid, skus, condition="Any", excludeme="False"):
        data = dict(Action='GetLowestOfferListingsForSKU',
                    MarketplaceId=marketplaceid,
                    ItemCondition=condition,
                    ExcludeMe=excludeme)
        data.update(self.enumerate_param('SellerSKUList.SellerSKU.', skus))
        return self.make_request(data)

    def get_lowest_offer_listings_for_asin(self, marketplaceid, asins, condition="Any", excludeme="False"):
        data = dict(Action='GetLowestOfferListingsForASIN',
                    MarketplaceId=marketplaceid,
                    ItemCondition=condition,
                    ExcludeMe=excludeme)
        data.update(self.enumerate_param('ASINList.ASIN.', asins))
        return self.make_request(data)

    def get_product_categories_for_sku(self, marketplaceid, sku):
        data = dict(Action='GetProductCategoriesForSKU',
                    MarketplaceId=marketplaceid,
                    SellerSKU=sku)
        return self.make_request(data)

    def get_product_categories_for_asin(self, marketplaceid, asin):
        data = dict(Action='GetProductCategoriesForASIN',
                    MarketplaceId=marketplaceid,
                    ASIN=asin)
        return self.make_request(data)

    def get_my_price_for_sku(self, marketplaceid, skus, condition=None):
        data = dict(Action='GetMyPriceForSKU',
                    MarketplaceId=marketplaceid,
                    ItemCondition=condition)
        data.update(self.enumerate_param('SellerSKUList.SellerSKU.', skus))
        return self.make_request(data)

    def get_my_price_for_asin(self, marketplaceid, asins, condition=None):
        data = dict(Action='GetMyPriceForASIN',
                    MarketplaceId=marketplaceid,
                    ItemCondition=condition)
        data.update(self.enumerate_param('ASINList.ASIN.', asins))
        return self.make_request(data)


class Sellers(MWS):
    """ Amazon MWS Sellers API """

    URI = '/Sellers/2011-07-01'
    VERSION = '2011-07-01'
    NS = '{http://mws.amazonservices.com/schema/Sellers/2011-07-01}'

    def list_marketplace_participations(self):
        """
            Returns a list of marketplaces a seller can participate in and
            a list of participations that include seller-specific information in that marketplace.
            The operation returns only those marketplaces where the seller's account is in an active state.
        """

        data = dict(Action='ListMarketplaceParticipations')
        return self.make_request(data)

    def list_marketplace_participations_by_next_token(self, token):
        """
            Takes a "NextToken" and returns the same information as "list_marketplace_participations".
            Based on the "NextToken".
        """
        data = dict(Action='ListMarketplaceParticipations', NextToken=token)
        return self.make_request(data)


#### Fulfillment APIs ####


class InboundShipments(MWS):
    URI = "/FulfillmentInboundShipment/2010-10-01"
    VERSION = '2010-10-01'

    # To be completed


class Inventory(MWS):
    """ Amazon MWS Inventory Fulfillment API """

    URI = '/FulfillmentInventory/2010-10-01'
    VERSION = '2010-10-01'
    NS = "{http://mws.amazonaws.com/FulfillmentInventory/2010-10-01}"

    def list_inventory_supply(self, skus=(), datetime=None, response_group='Basic'):
        """ Returns information on available inventory """

        data = dict(Action='ListInventorySupply',
                    QueryStartDateTime=datetime,
                    ResponseGroup=response_group,
                    )
        data.update(self.enumerate_param('SellerSkus.member.', skus))
        return self.make_request(data, "POST")

    def list_inventory_supply_by_next_token(self, token):
        data = dict(Action='ListInventorySupplyByNextToken', NextToken=token)
        return self.make_request(data, "POST")


class OutboundShipments(MWS):
    URI = "/FulfillmentOutboundShipment/2010-10-01"
    VERSION = "2010-10-01"
    # To be completed


class Recommendations(MWS):

    """ Amazon MWS Recommendations API """

    URI = '/Recommendations/2013-04-01'
    VERSION = '2013-04-01'
    NS = "{https://mws.amazonservices.com/Recommendations/2013-04-01}"

    def get_last_updated_time_for_recommendations(self, marketplaceid):
        """
        Checks whether there are active recommendations for each category for the given marketplace, and if there are,
        returns the time when recommendations were last updated for each category.
        """

        data = dict(Action='GetLastUpdatedTimeForRecommendations',
                    MarketplaceId=marketplaceid)
        return self.make_request(data, "POST")

    def list_recommendations(self, marketplaceid, recommendationcategory=None):
        """
        Returns your active recommendations for a specific category or for all categories for a specific marketplace.
        """

        data = dict(Action="ListRecommendations",
                    MarketplaceId=marketplaceid,
                    RecommendationCategory=recommendationcategory)
        return self.make_request(data, "POST")

    def list_recommendations_by_next_token(self, token):
        """
        Returns the next page of recommendations using the NextToken parameter.
        """

        data = dict(Action="ListRecommendationsByNextToken",
                    NextToken=token)
        return self.make_request(data, "POST")

if __name__ == '__main__':
    # key&pwd是开发者账号的
    access_key = "AKIAJCZD4ZNPVBU36WKQ"
    secret_key = "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"
    # 抓取的是账号amazon
    account_id = "A3THBIK7QYKUUV"
    auth_token = "amzn.mws.7ea98e1b-7f63-e99e-e945-72d8ee6099ae"

    _orders = Orders(access_key=access_key, secret_key=secret_key, account_id=account_id, region='US', auth_token=auth_token)

    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    pp.pprint(_orders.list_orders(marketplaceids=["ATVPDKIKX0DER",], lastupdatedafter="2016-01-01", max_results="50", fulfillment_channels=('AFN',)).parsed)
    pp.pprint(_orders.get_order(['115-2593391-4441000',]).parsed)
    pp.pprint(_orders.list_orders_by_next_token(token="gGtvrTT8Wa+v06krKetbKrtwX7u5furPkr1n0nQYpwbNeGyEmOrLe7q8xqAchQNKurwYODTEdypxJYAo4rlJ28IaMN1OPK6aQoh/yuPOcVfK9kUavBVIe6I4GnWh00CCBmDEpgcMx5yRSMvP4Q3g57uZIF9n45mtnrZ4AbBdBTd4Locah6SamDUAW7SQEcD8kSIjO9qlPaRnuRNsIPkVTh+z+Y0y5tluXT51CrLPlUdUF5G6AXB5ffOhYyV6SQjbbuONMlPzOzW92aHYm7zAoF1+VTWe5H3ccSWAKOK5SdtMy+fzBc3vTeiccPYcDRxrWi5999oXve7FEz8Y4D26rypRPH1WXWq8ibpvelRy2yu7EbcPNB+bB5CkgT8s+oRK11Ds5w1QtjWMUNy+Jr7PYjOPK+Zzoe2U7Xj1H2rDgJYELp2I5DB1V4nVWIh1Jo+KRGvmHdX0hi9hYJ3/LXjgKmZV6Ecejl5BPMG4jNqghnlDZBmR6xJsElFWFRtCfy55tspPXiBISAldESNo6FccQ67zwIG36Cdw4JHWT14XEXDTlgeonr9kKDTlyfVjZMRX").parsed)
    pp.pprint(_orders.list_order_items(amazon_order_id="107-7213591-0037068").parsed)
    
# # _products = Products(access_key=access_key, secret_key=secret_key, account_id=account_id, region='US', auth_token=auth_token)


# # print _orders.get_service_status().parsed

#pp.pprint(_products.get_product_categories_for_asin(marketplaceid="ATVPDKIKX0DER", asin="B0163CHND0").parsed)

# asins= ["B00BGA9X9W", "B00YQ2KCWO", "B00W8FYF56", "B00VU4J13W", "B00OQVZDJM" ]
# asins= ["B00Y7S05YC","B00Y7S06OG","B00YXNC4HW","B00Y7S06PK","B00NB4QQ5K","B00YXNE3BW","B00YXNEG9Q","B00YXNEGYQ","B00Y7JE3P8","B00Y7JE3NA","B00Y7S06NM","B00Y7S06O6","B00NB4QNJO","B00Y7S060U","B00Y7JE3US","B00Y7S05X8","B00Y7S05YW","B00XHHA3KK","B00Y7JE3VW","B00Y7S06QE","B00XHHA4PE","B00YXNCX64","B010LNQ4SC","B00Y7N5858","B00YXNDAJ8","B00YXNDG0Q","B00YXNDMAA","B00Y7N59N4","B00YXNC8KU","B00YXND3SQ","B010LNQBBW","B00YXNE4YS","B00YXNCXDM","B00Y7LA04E","B00Y7N59PM","B00YXNCPZI","B00YXNDCY6","B00YXNEZBA","B010LNPYWE","B00NB4QYIY","B00NB4R1BI","B00NB4QYIY","B00NB4R1BI","B00NB4R5XW","B00X3GZ53K","B00NB4R54G","B00NB4R474","B00NB4R5XW","B00NB4R54G","B00NB4R474","B00X3GZ53K","B00Y7GWF3S","B00Y7GWEGQ","B00NB4RBKE","B00NB4RBKE","B00NB4RDPC","B00NB4RF1O","B00NB4RF1O","B00NB4RFZ0","B00NB4RL9U","B00NB4S662","B00PGZPFXQ","B00PW05FTE","B00NB4QKHO","B00NB4QJIO","B00NB4QKHO","B00NB4QLE6","B00NB4QJIO","B00NB4QN9O","B00NB4QP2O","B00NB4RM3A","B00NURC41S","B00NURC41S","B00NURBTXW","B00NURC288","B00NURC288","B00NURCNGY","B00NURBTX2","B00NURBTX2","B00NUXOKPU","B00OZELEZC","B00OZELK7Y","B00OZELM2C","B00NUXOFKA","B00OZELLEG","B00OZELGD2","B00OZELJ5W","B00S4R5VVE","B00S4R5XLM","B00NUXO86G","B00NUXOOME","B00OZELGPU","B00OZELEY8","B00S4R5U7E","B00NUXOKPU","B00OZELHWW","B00NUXO86G","B00S4R5U7E","B00S4R5XLM","B00NUXOFKA",][0:20]
# asins = ['B00EW6QT76', 'B00WUKULAC', 'B0163CHND0', 'B016OFYGXQ', 'B00XKRWTUE']

#aaaaaaaaaaaaaaaaaaaaaaaaaaaaa #pp.pprint(_products.get_lowest_offer_listings_for_asin(marketplaceid="ATVPDKIKX0DER", asins=asins, condition="new").parsed)
# items = _products.get_lowest_offer_listings_for_asin(marketplaceid="ATVPDKIKX0DER", asins=asins, condition="new").parsed

# for item in items:
#     #pp.pprint(item)
#     print '------'
#     print item['@ASIN']
#     for price_item in item['Product']['LowestOfferListings']['LowestOfferListing']:
#         #print price_item['Price']['LandedPrice']['Amount']
#         print price_item['Price']['ListingPrice']['Amount']
#         #print price_item['Price']['Shipping']['Amount']

# #pp.pprint(_products.get_competitive_pricing_for_asin(marketplaceid="ATVPDKIKX0DER", asins=asins).parsed)
# # pp.pprint(_products.get_matching_product(marketplaceid="ATVPDKIKX0DER", asins=asins).parsed)
# print '-----------------------'
# # pp.pprint(_products.get_product_categories_for_asin(marketplaceid="ATVPDKIKX0DER", asin="B00OQVZDJM").parsed)

# pp.pprint(_products.list_matching_products(marketplaceid="ATVPDKIKX0DER", query="dress").parsed)
