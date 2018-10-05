#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector

class myConn:
	"""Парсим конфиг и инициализируем коннект к базе данных"""
	def __init__(self, conf):
		try:
			print('Try read config')
			self.__host = conf['host']
			self.__user = conf['user']
			self.__pass = conf.get('pass')
			self.__db = conf['db']
		except:
			print('Fail to read config')
			raise SystemExit()
		print("Success!")
		self.connect()

	"""пробуем законнкетиться"""
	def connect(self):
		try:
			print("Try connect DB")
			self.__dbc = mysql.connector.connect(
				host=self.__host, 
				user=self.__user, 
				password=self.__pass, 
				database=self.__db
			)
		except:
			print('Fail to connect!')
			raise SystemExit()
		print("Success!")

	def __del__(self):
		self.__dbc.close()

	"""Выполняем  sql-запрос"""
	def execute(self, sql, list=None):
		cur = self.__dbc.cursor()
		res = None
		if sql[:6].lower() == 'insert':
			cur.execute(sql, list)
		elif sql[:6].lower() == 'select':
			cur.execute(sql, list)
			res = cur.fetchall()
		elif sql[:6].lower() == 'delete':
			cur.execute(sql, list)
		elif sql[:6].lower() == 'update':
			cur.execute(sql, list)
		cur.close()
		return res
	
	"""выполняем множественный sql-запрос"""
	def execute_many(self, sql, list):
		if len(list) != 0:
			cur = self.__dbc.cursor()
			cur.executemany(sql, list)
			cur.close()
		
	"""подтверждаем изменения в DB"""
	def commit(self):
		self.__dbc.commit()
