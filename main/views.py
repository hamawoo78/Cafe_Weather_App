from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render
from django.http import HttpResponse
import requests
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView

from django.urls import reverse_lazy
from django import forms

from .models import Shop, Data
from django.apps import apps

import json
import math
from django.http import HttpResponseServerError

# Create your views here.

class ShopList(ListView):
    model = Shop
    fields = ['location']
    template_name = 'index.html'
    context_object_name = "shops"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_input = self.request.GET.get('year_month') or '2022-09'
        # print(type(user_input))
        year = user_input[:4]
        input_month = int(user_input[5:7])
        month = str(input_month).zfill(2)
        context['year'] = year
        context['month'] = month
        context['yearmonth'] = year + '-' + month

        ave_data_list = {}
        forecast_data_list = {}


        for shop in context['shops']:
            # tempurture info
            geocode = f"{shop.lat},{shop.lng}"
            ave_data = self.get_weather_data(geocode, year, month) 
            ave_data_list[shop.id] = ave_data  
            # get value from dictionary
            shop.ave_data = ave_data_list.get(shop.id) 
            # (14, 65, 14, 31, 26)  
            # print(shop.ave_data)

            ave_data = list(ave_data)
            for i in [3, 4]:
                if ave_data[i] >= 27 and ave_data[i] < 34 and ave_data[i] % 2 != 0:
                    ave_data[i] += 1
                elif ave_data[i] == 45:
                    ave_data[i] = 39
                elif ave_data[i] == 46:
                    ave_data[i] = 41
                elif ave_data[i] == 47:
                    ave_data[i] = 38
            shop.top = f"img/{ave_data[3]}.png"
            shop.second = f"img/{ave_data[4]}.png"

            # forecast info
            forecast_data_instance = ForecastData()
            forecast = forecast_data_instance.get_forecast_data(geocode)
            # print(forecast) ([11, 12], [30, 29], 23, 26)  

            forecast_data_list[shop.id] = forecast
            shop.forecast_data = forecast_data_list.get(shop.id) 
            shop.today_D = f"img/{forecast[0][0]}.png"
            shop.today_N = f"img/{forecast[0][1]}.png"
            shop.tomorrow_D = f"img/{forecast[1][0]}.png"
            shop.tomorrow_N = f"img/{forecast[1][1]}.png"

        return context

    def get_weather_data(self, geocode, year, month):
        # print("i am in get weather in list view class")
        day = ForecastData()
        day = day.get_day(year, month)

        api_url = f'https://api.weather.com/v3/wx/hod/r1/direct?geocode={geocode}&startDateTime={year}-{month}-01T00:00:00Z&endDateTime={year}-{month}-{day}T00:00:00Z&format=json&units=m&apiKey=7698370dea91420198370dea91720199'
        # print(api_url)

        try:
            response = requests.get(api_url)

            weather_data = json.loads(response.content)
            # print(weather_data)
            ave_temp = 0
            sum_temp = 0

            ave_humid = 0
            sum_humid = 0

            ave_feels = 0
            sum_feels = 0
            count = 0

            icon = {}

            for temp_data, humid_data, feels_data, code in zip(weather_data['temperature'], weather_data['relativeHumidity'], weather_data['temperatureFeelsLike'], weather_data['iconCode']):
                sum_temp += temp_data
                sum_humid += humid_data
                sum_feels += feels_data
                count += 1

                if code not in icon:
                    icon[code] = 1
                else:
                    icon[code] += 1

            sorted_icon = dict(sorted(icon.items(), key=lambda x:x[1], reverse=True))
            # print(sorted_icon)
            # {26: 100, 28: 77, 27: 53, 11: 15, 29: 72, 31: 119, 32: 94, 34: 33, 33: 40, 30: 54, 12: 38, 40: 1}
            top_icon = list(sorted_icon.keys())[0]
            second_icon = list(sorted_icon.keys())[1]
            
            ave_temp = math.floor(sum_temp/count)
            ave_humid = math.floor(sum_humid/count)
            ave_feels = math.floor(sum_feels/count)
            # print(ave_temp)
            return ave_temp, ave_humid, ave_feels, top_icon, second_icon
        
        except json.JSONDecodeError:
            response = HttpResponse("Error")
            return response
    

class MoreDetail(DetailView):
    model = Shop
    fields = ['location']
    template_name = 'detail.html'
    context_object_name = "shop"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_input = self.request.GET.get('year_month') or self.kwargs.get('yearmonth')
        # print(user_input)

        year = user_input[:4]

        input_month = int(user_input[5:7])
        month = str(input_month).zfill(2)

        shop = context['shop']
        # print(shop)
        geocode = f"{shop.lat},{shop.lng}"
        ave_data = self.get_weather_data(geocode, year, month)
        # print(ave_data) 

        for i in range(3):
            if ave_data[i][3] >= 27 and ave_data[i][3] < 34 and ave_data[i][3] % 2 != 0:
                ave_data[i][3] += 1
            elif ave_data[i][3] == 45:
                ave_data[i][3] = 39
            elif ave_data[i][3] == 46:
                ave_data[i][3] = 41
            elif ave_data[i][3] == 47:
                ave_data[i][3] = 38

        top_b = f"img/{ave_data[0][3]}.png"
        top_m = f"img/{ave_data[1][3]}.png"
        top_l = f"img/{ave_data[2][3]}.png"
        # print(top_b)

        if not ave_data:
            # Handle the case when ave_data is empty (no JSON response)
            return HttpResponseServerError("No weather data available.")

        forecast_data_list = {}
        shops = Shop.objects.all()
        context = {
            'ave_data': ave_data,
            'shops' : shops,
            'shop' : shop,
            'top_b': top_b,
            'top_m': top_m,
            'top_l': top_l,
            'yearmonth' : year + '-' + month,
            'year' : year,
            'month' :month
        }
        # print(shop)

        for shop in shops:
            # forecast info
            forecast_data_instance = ForecastData()
            forecast = forecast_data_instance.get_forecast_data(geocode)
            # print(forecast)('Cloudy/Rain', 'Rain') 
            # print(forecast)

            forecast_data_list[shop.id] = forecast
            shop.forecast_data = forecast_data_list.get(shop.id) 
            shop.today_D = f"img/{forecast[0][0]}.png"
            shop.today_N = f"img/{forecast[0][1]}.png"
            shop.tomorrow_D = f"img/{forecast[1][0]}.png"
            shop.tomorrow_N = f"img/{forecast[1][1]}.png"

        return context

    def get_weather_data(self, geocode, year, month):
        day = ForecastData()
        day = day.get_day(year, month)

        api_url = f'https://api.weather.com/v3/wx/hod/r1/direct?geocode={geocode}&startDateTime={year}-{month}-01T00:00:00Z&endDateTime={year}-{month}-{day}T23:20:00Z&format=json&units=m&apiKey=7698370dea91420198370dea91720199'
        
        try:
            response = requests.get(api_url)

            weather_data = json.loads(response.content)
            # print(weather_data)
            count_b = 0
            count_m = 0
            count_l = 0
            sum_temp = 0
            sum_humid = 0
            sum_feels = 0
            icon = {}

            for date in weather_data['validTimeUtc']:
                day = int(date[8:10])
                pointer = int(date[11:13])
                num = weather_data['validTimeUtc'].index(date)

                if day <= 10 :
                    beginning_sum_data = self.calculate_weather_data(weather_data, num, pointer, sum_temp, sum_humid, sum_feels, icon)
                    count_b =+ 1
                    
                    if pointer == 23:
                        beginning_ave_data = self.get_ave_weather_data(beginning_sum_data, count_b)

                elif day >= 11 and day <= 20:
                    middle_sum_data = self.calculate_weather_data(weather_data, num, pointer, sum_temp, sum_humid, sum_feels, icon)
                    count_m =+ 1
                    
                    if pointer == 23:
                        middle_ave_data = self.get_ave_weather_data(middle_sum_data, count_m)
                else:
                    last_sum_data = self.calculate_weather_data(weather_data, num, pointer, sum_temp, sum_humid, sum_feels, icon)
                    count_l =+ 1
                    
                    if pointer == 23:
                        last_ave_data = self.get_ave_weather_data(last_sum_data, count_l)
            
            return beginning_ave_data, middle_ave_data, last_ave_data
        
        except json.JSONDecodeError:
            response = HttpResponse("Error")
            return response

    
    def calculate_weather_data(self, weather_data, num, pointer, sum_temp, sum_humid, sum_feels, icon):
        sum_temp += weather_data['temperature'][num]
        sum_humid += weather_data['relativeHumidity'][num]
        sum_feels += weather_data['temperatureFeelsLike'][num]
        if weather_data['iconCode'][num] not in icon:
            icon[weather_data['iconCode'][num]] = 1
        else:
            icon[weather_data['iconCode'][num]] += 1
        
        sorted_icon = dict(sorted(icon.items(), key=lambda x:x[1], reverse=True))
        top_icon = list(sorted_icon.keys())[0]
        # print(top_icon)

        if pointer == 23:
            sum = []
            sum.append(sum_temp)
            sum.append(sum_humid)
            sum.append(sum_feels)
            sum.append(top_icon)

            sum_temp = 0
            sum_humid = 0
            sum_feels = 0
            icon = {}

            return sum
        else:
            return

    def get_ave_weather_data(self, weather_data, num):
        data=[]
        ave_temp = math.floor(weather_data[0]/num)
        ave_humid = math.floor(weather_data[1]/num)
        ave_feels = math.floor(weather_data[2]/num)
        data.append(ave_temp)
        data.append(ave_humid)
        data.append(ave_feels)
        data.append(weather_data[3])

        ave_temp = 0
        ave_humid = 0
        ave_feels = 0
        

        return data
    
class AddNewLocation(CreateView):   
    model = Shop
    fields = '__all__'
    template_name = 'add_form.html'
    context_object_name = "shop"
    
    def get_success_url(self):
        return reverse_lazy('index')

class SalesList(ListView):
    model = Data
    fields = '__all__'
    template_name = 'sales.html'
    context_object_name = "datas"

    def get_context_data(self, **kwargs):
        # forecast info
        context = super().get_context_data(**kwargs)
        forecast_data_list = {}
        shops = Shop.objects.all()
        for shop in shops:
            # forecast info
            # print(shop)
            geocode = f"{shop.lat},{shop.lng}"
            forecast_data_instance = ForecastData()
            forecast = forecast_data_instance.get_forecast_data(geocode)

            # print(forecast)

            forecast_data_list[shop.id] = forecast
            shop.forecast_data = forecast_data_list.get(shop.id) 
            shop.today_D = f"img/{forecast[0][0]}.png"
            shop.today_N = f"img/{forecast[0][1]}.png"
            shop.tomorrow_D = f"img/{forecast[1][0]}.png"
            shop.tomorrow_N = f"img/{forecast[1][1]}.png"

        context['shops'] = shops
        return context


class AddSales(CreateView):   
    model = Data
    fields = ['location', 'sales', 'Temp','humid']
    template_name = 'add_form.html'
    context_object_name = "data"

    def get_context_data(self, **kwargs):
    # forecast info
        context = super().get_context_data(**kwargs)
        forecast_data_list = {}
        shops = Shop.objects.all()
        for shop in shops:
            # forecast info
            # print(shop)
            geocode = f"{shop.lat},{shop.lng}"
            forecast_data_instance = ForecastData()
            forecast = forecast_data_instance.get_forecast_data(geocode)

            # print(forecast)

            forecast_data_list[shop.id] = forecast
            shop.forecast_data = forecast_data_list.get(shop.id) 
            shop.today_D = f"img/{forecast[0][0]}.png"
            shop.today_N = f"img/{forecast[0][1]}.png"
            shop.tomorrow_D = f"img/{forecast[1][0]}.png"
            shop.tomorrow_N = f"img/{forecast[1][1]}.png"

        context['shops'] = shops
        return context
    
    def get_success_url(self):
        return reverse_lazy('sales')
    


class ForecastData:
    def get_day(self,year, month):
        if month == 2:
            if year % 4 == 0:
                if year % 100 == 0 and not year % 400 != 0:
                    day = 28
                else:
                    day = 29
            else:
                day = 28
        elif month == 4 or month == 6 or month == 9 or month == 11 :
            day = 30
        else:
            day = 31
        
        return day

    def get_forecast_data(self, geocode):
        data_list = {}
        api_url = f'https://api.weather.com/v3/wx/forecast/hourly/2day?geocode={geocode}&format=json&units=m&language=en-EN&apiKey=7698370dea91420198370dea91720199'
        
        try:
            response = requests.get(api_url)
            weather_data = json.loads(response.content)
            # print(weather_data)

            forecast_list_D = {}
            forecast_list_N = {}
            pointer = ''
            sign = 0
            ave_temp_today = 0
            ave_temp_tomorrow = 0
            sum_temp = 0
            count = 0

            for day, dn, forecast, temp  in zip(weather_data['dayOfWeek'] ,weather_data['dayOrNight'], weather_data['iconCode'], weather_data['temperature']):
                if pointer == '' or pointer == day:
                    pointer = day
                    sum_temp += temp
                    count += 1
                    if dn == "D":
                        if forecast in forecast_list_D:
                            forecast_list_D[forecast] += 1
                        else:
                            forecast_list_D[forecast] = 1
                    else:
                        if forecast in forecast_list_N:
                            forecast_list_N[forecast] += 1
                        else:
                            forecast_list_N[forecast] = 1
                else:
                    pointer = ''
                    sorted_forecast_D = sorted(forecast_list_D.items(), key=lambda x:x[1], reverse=True)
                    sorted_forecast_N = sorted(forecast_list_N.items(), key=lambda x:x[1], reverse=True)
                    forecast_D = sorted_forecast_D [0][0]
                    forecast_N = sorted_forecast_N [0][0]

                    if sign == 0:
                        sign = 1
                        forecast_today = []
                        ave_temp_today = math.floor(sum_temp/count)
                        forecast_today.append(forecast_D)
                        forecast_today.append(forecast_N)
                    else:
                        ave_temp_tomorrow = math.floor(sum_temp/count)
                        forecast_tomorrow = []
                        forecast_tomorrow.append(forecast_D)
                        forecast_tomorrow.append(forecast_N)                    

            return forecast_today, forecast_tomorrow, ave_temp_today, ave_temp_tomorrow
        
        except json.JSONDecodeError:
            response = HttpResponse("Error")
            return response
        
class MyView(TemplateView):
    template_name = 'main.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allowed_url_names'] = ['index', 'detail', 'add']
        return context