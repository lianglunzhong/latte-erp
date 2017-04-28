# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from rest_framework import routers, serializers, viewsets
from product.models import Category,  Product, Item
from order.models import Order, OrderItem

# Serializers define the API representation.
#serializers.HyperlinkedModelSerializer 和serializers.ModelSerializer 都可以
class UserSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_staff', 'is_active')

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

#TODO product
#serializers.HyperlinkedModelSerializer括号里写这个报错
class CategorySerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'parent', 'brief', 'status')

class ItemSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = Item
        #fields = ('order', 'title')

class ProductSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    items = ItemSerializer(many=True)

    class Meta:
        model = Product

class OrderItemSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem

class OrderSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order 



# class ProductSerializer(serializers.Serializer):
#     pk = serializers.IntegerField(read_only=True)
#     # title = serializers.CharField(required=False, allow_blank=True, max_length=100)
#     # code = serializers.CharField(style={'base_template': 'textarea.html'})
#     # linenos = serializers.BooleanField(required=False)
#     # language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, default='python')
#     # style = serializers.ChoiceField(choices=STYLE_CHOICES, default='friendly')
#
#     category = serializers.CharField(Category)
#     name = serializers.CharField(max_length=300)
#     cost = serializers.CharField(default=0.0)
#
#     status = serializers.CharField(default=True, choices=PRODUCT_STATUS)
#     brief = serializers.CharField(blank=True, null=True)
#     description = serializers.CharField(blank=True, null=True, default='')
#     note = serializers.CharField(blank=True, null=True, default='')
#     weight = serializers.CharField(default=0.0, help_text=u"基本单位为KG 千克")
#
#     options = serializers.CharField(Option, blank=True)
#
#     def create(self, validated_data):
#         """
#         Create and return a new `Snippet` instance, given the validated data.
#         """
#         return Snippet.objects.create(**validated_data)
#
#     def update(self, instance, validated_data):
#         """
#         Update and return an existing `Snippet` instance, given the validated data.
#         """
#         instance.title = validated_data.get('title', instance.title)
#         instance.code = validated_data.get('code', instance.code)
#         instance.linenos = validated_data.get('linenos', instance.linenos)
#         instance.language = validated_data.get('language', instance.language)
#         instance.style = validated_data.get('style', instance.style)
#         instance.save()
#         return instance
