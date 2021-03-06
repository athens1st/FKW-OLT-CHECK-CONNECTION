from django.shortcuts import render
import paramiko
from scp import SCPClient
import os, os.path, sys, socket, time, datetime
import shutil
import json
# import StringIO
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, FileResponse
from django.contrib import messages
from .forms import NacmForm, IpFormset, UploadForm, SettingForm
from . import models
from .models import Connect, c_Setting as settings
from . import serializers
from .functions.functions import handle_uploaded_file
from rest_framework import generics
from netaddr import IPAddress, IPNetwork
from django.utils.crypto import get_random_string
import subprocess as sp
from django.views import View
import zipfile
from io import BytesIO

ip_list = []
# zxc = None
# formm = None  
# ipform = None 
# upform = None 
# userValue = None 
# passValue = None 
# confValue = None 

def index(request):
	tests = "test"
	print (tests)

# def connect(request):
# 	# formm = NacmForm(request.POST or None)
# 	# ipform = IpFormset(request.POST)
# 	upform = UploadForm(request.POST,request.FILES)
# 	userValue = formm['username'].value()
# 	passValue = formm['password'].value()
# 	confValue = formm['conft'].value()

class config_codeBased(View):

	ip_list = []
	status = ''
	value_bak = 1
	# backup_dir = "/var/www/nacm/backup/"

	def post(self, request, *args, **kwargs):
		formm = NacmForm(request.POST or None)
		ipform = IpFormset(request.POST)
		# connect(request)
		upform = UploadForm(request.POST,request.FILES)
		userValue = formm['username'].value()
		passValue = formm['password'].value()
		confValue = formm['conft'].value()
		print(confValue+'atas')
		# connect(request)
		# print (zxc)
		# print (ipform.is_valid())
		generator = get_random_string(length=8)
		# usernamef = get_object_or_404(Connect, pk=id)
		if ipform.is_valid() and formm.is_valid():
			simpanForm = formm.save()
			for form in ipform:
				ipaddr = form.cleaned_data.get('ipaddr')
				vendor = form.cleaned_data.get('vendor')
				collect_config = "<b>Configure on "+str(ipaddr)+" | vendor = "+str(vendor)+"</b></br>"
				print (vendor)
				try:
					ssh_client = paramiko.SSHClient()
					ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					ssh_client.connect(hostname=ipaddr,username=userValue,password=passValue)
					# ssh_client.exec_command(confValue)
					remote_conn=ssh_client.invoke_shell()
					output = remote_conn.recv(65535)
					try:
						print("try exec command")
						ssh_client.exec_command(confValue+"\n")
						print(confValue+'bawah')
						time.sleep(1)
					except:
						try:
							print("try shell interactive")
							remote_conn.send(confValue+"\n")
							time.sleep(1)
						except:
							print ("error paramiko")
					# print (output)
					# print (stdout.read())
					paramiko.util.log_to_file("filename.log")					
					simpanIp = form.save(commit=False)
					messages.success(request, collect_config)
					simpanIp.connect_id = simpanForm
					print (simpanIp)
					simpanIp.save()
					ssh_client.close()
					simpanForm.save()
					
				except paramiko.AuthenticationException:
					print ("Authentication failed, please verify your credentials")
					conf_error = collect_config+"</br>Authentication failed, please verify your credentials"
					messages.error(request, conf_error)
					result_flag = False
				except paramiko.SSHException as sshException:
					print ("Could not establish SSH connection: %s" % sshException)
					conf_error = collect_config+"</br>Could not establish SSH connection: %s" % sshException
					messages.error(request, conf_error)
					result_flag = False
				except socket.timeout as e:
					print ("Connection timed out")
					conf_error = collect_config+"</br>Connection timed out"
					messages.error(request, conf_error)
					result_flag = False
				except Exception as e:
					print ("Exception in connecting to the server")
					print ("PYTHON SAYS:",e)
					conf_error = collect_config+"</br>Exception in connecting to the server"
					messages.error(request, conf_error)
					result_flag = False
					self.client.close()
				
		return HttpResponseRedirect('code_based')

	def get(self, request, *args, **kwargs):
		formm = NacmForm()
		ipform = IpFormset()
		return render(request, 'config/code_based.html', {'form': formm, 'logins': Connect.objects.all(), 'ipform': ipform, 'status': self.status })


class config_static(View):
	ip_list = []
	status = ''
	value_bak = 1

	def post(self, request, *args, **kwargs):
	# if request.method == 'POST':
		formm = NacmForm(request.POST or None)
		ipform = IpFormset(request.POST)
		upform = UploadForm(request.POST,request.FILES)
		userValue = formm['username'].value()
		passValue = formm['password'].value()
		destination = str(request.POST['destination'])
		prefix = str(request.POST['prefix'])
		gateway = str(request.POST['gateway'])
		localfilepath = os.getcwd()
		staticDir = localfilepath+"/plugin/config/routing/static/"
		if ipform.is_valid() and formm.is_valid():
			simpanForm = formm.save()

			for form in ipform:
				ipaddr = form.cleaned_data.get('ipaddr')
				vendor = form.cleaned_data.get('vendor')
				networks = str(destination+"/"+prefix)
				netmask = IPNetwork(networks).netmask
				collect_config = "<b>Configure on "+str(ipaddr)+" | vendor = "+str(vendor)+"</b></br>"
				print (netmask)
				print (prefix)
				# print (localfilepath)
				try:
					ssh_client = paramiko.SSHClient()
					ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					ssh_client.connect(hostname=ipaddr,username=userValue,password=passValue,look_for_keys=False, allow_agent=False, timeout=5)
					remote_conn=ssh_client.invoke_shell()
					shell = remote_conn.recv(65535)
					config_read = str(vendor.sett_static_routing)
					# split memakai \r dulu
					array_read = config_read.split('\r')
					# hasilnya akan ada \n
					output_line = ""
					# print (array_read)

					for line in array_read:
						# menghilangkan \n
						new_line = re.sub(r'\n','',line)
						# print new_line
						# akan error karena ada nilai kosong dan eval tidak bisa membacanya
						# sehingga mengeleminasi nilai kosong
						if new_line != '':
							config_send = eval(new_line)
							collect_config = collect_config + config_send+"</br>" 
							print(config_send+" ini config send")
							try:
								stdin, stdout, stderr = ssh_client.exec_command(config_send+"\n")
								time.sleep(1)
								results = stdout.read()
								print (str(results))
							except:
								try:
									remote_conn.send(config_send+"\n")
									time.sleep(1)
									results = remote_conn.recv(65535)
									print (results.decode('ascii'))
									# print (results)
								except:
									print("error paramiko")
					messages.success(request, collect_config)
					
					ssh_client.close()
					paramiko.util.log_to_file("filename.log")
					simpanIp = form.save(commit=False)
					simpanIp.connect_id = simpanForm
					print (simpanIp)
					simpanIp.save()

					simpanForm.save()

				except paramiko.AuthenticationException:
					print ("Authentication failed, please verify your credentials")
					conf_error = collect_config+"</br>Authentication failed, please verify your credentials"
					messages.error(request, conf_error)
					result_flag = False
				except paramiko.SSHException as sshException:
					print ("Could not establish SSH connection: %s" % sshException)
					conf_error = collect_config+"</br>Could not establish SSH connection: %s" % sshException
					messages.error(request, conf_error)
					result_flag = False
				except socket.timeout as e:
					print ("Connection timed out")
					conf_error = collect_config+"</br>Connection timed out"
					messages.error(request, conf_error)
					result_flag = False
				except Exception as e:
					print ("Exception in connecting to the server")
					print ("PYTHON SAYS:",e)
					conf_error = collect_config+"</br>Exception in connecting to the server"
					messages.error(request, conf_error)
					result_flag = False
					self.client.close()

		return HttpResponseRedirect('routing_static')
		
	def get(self, request, *args, **kwargs):
		formm = NacmForm()
		ipform = IpFormset()
		return render(request, 'config/routing_static.html', {'form': formm, 'logins': Connect.objects.all(), 'ipform': ipform, 'status': self.status})

class config_dynamic(View):
	ip_list = []
	status = ''
	value_bak = 1

	def post(self, request, *args, **kwargs):
		formm = NacmForm(request.POST or None)
		ipform = IpFormset(request.POST)
		upform = UploadForm(request.POST,request.FILES)
		userValue = formm['username'].value()
		passValue = formm['password'].value()
		confValue = formm['conft'].value()
		rd_select = str(request.POST['dynamic_routing_select'])
		print(rd_select)
		id_ospf = str(request.POST['id_ospf'])
		router_id = str(request.POST['rid_ospf'])
		print(router_id)
		network = str(request.POST['network_ospf'] or request.POST['network_ripv1'] or request.POST['network_ripv2'])
		print (network)
		prefix = str(request.POST['prefix_ospf'] or request.POST['prefix_ripv1'] or request.POST['prefix_ripv2'])
		area = str(request.POST['area'])
		interface_ospf = str(request.POST['interface_ospf'])
		generator = get_random_string(length=8)
		if ipform.is_valid() and formm.is_valid():
			simpanForm = formm.save()
			for form in ipform:
				ipaddr = form.cleaned_data.get('ipaddr')
				vendor = form.cleaned_data.get('vendor')
				networks = netmask = wildcard = ""
				if prefix != '':
					networks = str(network+"/"+prefix)
					print(networks)
					netmask = IPNetwork(networks).netmask
					print(netmask)
					wildcard = IPNetwork(networks).hostmask
					print(wildcard)
					print (vendor)
				ssh_client = paramiko.SSHClient()
				ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				ssh_client.connect(hostname=ipaddr,username=userValue,password=passValue)
				remote_conn=ssh_client.invoke_shell()
				output = remote_conn.recv(65535)
				config_read = None
				if rd_select == 'ospf':
					config_read = str(vendor.sett_dynamic_routing_ospf)
				elif rd_select == 'ripv1':
					config_read = str(vendor.sett_dynamic_routing_ripv1)
				elif rd_select == 'ripv2':
					config_read = str(vendor.sett_dynamic_routing_ripv2)
				# split memakai \r dulu
				array_read = config_read.split('\r')
				# hasilnya akan ada \n
				counter = 0
				for line in array_read:
					# menghilangkan \n
					new_line = re.sub(r'\n','',line)
					# print new_line
					# akan error karena ada nilai kosong dan eval tidak bisa membacanya
					# sehingga mengeleminasi nilai kosong
					if new_line != '':
						config_send = eval(new_line)
						print(config_send)
						try:
							ssh_client.exec_command(config_send+"\n")
							time.sleep(1)
						except:
							try:
								if counter == 0:
									print("try shell interactive")
									counter+=1
								remote_conn.send(config_send+"\n")
								time.sleep(1)
							except:
								print("error paramiko")
				
				ssh_client.close()
				
				paramiko.util.log_to_file("filename.log")
				simpanIp = form.save(commit=False)
				simpanIp.connect_id = simpanForm
				print (simpanIp)
				simpanIp.save()

			simpanForm.save()

		return HttpResponseRedirect('routing_dynamic')

	def get(self, request, *args, **kwargs):
		formm = NacmForm()
		ipform = IpFormset()
		return render(request, 'config/routing_dynamic.html', {'form': formm, 'logins': Connect.objects.all(), 'ipform': ipform, 'status': self.status })

class config_bgp(View):
	ip_list = []
	status = ''
	value_bak = 1

	def post(self, request, *args, **kwargs):
		formm = NacmForm(request.POST or None)
		ipform = IpFormset(request.POST)
		upform = UploadForm(request.POST,request.FILES)
		userValue = formm['username'].value()
		passValue = formm['password'].value()
		confValue = formm['conft'].value()
		generator = get_random_string(length=8)
		if ipform.is_valid() and formm.is_valid():
			simpanForm = formm.save()
			for form in ipform:
				ipaddr = form.cleaned_data.get('ipaddr')
				vendor = form.cleaned_data.get('vendor')
				print (vendor)
				ssh_client = paramiko.SSHClient()
				ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				ssh_client.connect(hostname=ipaddr,username=userValue,password=passValue)
				remote_conn=ssh_client.invoke_shell()
				output = remote_conn.recv(65535)
				stdin,stdout,stderr = ssh_client.exec_command(confValue)
				time.sleep(1)
				print (output)
				print (stdout.read())
				simpanIp = form.save(commit=False)
				simpanIp.connect_id = simpanForm
				print (simpanIp)
				simpanIp.save()

			simpanForm.save()

		return HttpResponseRedirect('config/routing_bgp')
	def get(self, request, *args, **kwargs):
		formm = NacmForm()
		ipform = IpFormset()
		return render(request, 'config/routing_bgp.html', {'form': formm, 'logins': Connect.objects.all(), 'ipform': ipform, 'status': status })

class vlan(View):
	ip_list = []
	status = ''
	value_bak = 1

	def post(self, request, *args, **kwargs):
		formm = NacmForm(request.POST or None)
		ipform = IpFormset(request.POST)
		upform = UploadForm(request.POST,request.FILES)
		userValue = formm['username'].value()
		passValue = formm['password'].value()
		confValue = formm['conft'].value()
		generator = get_random_string(length=8)
		if ipform.is_valid() and formm.is_valid():
			simpanForm = formm.save()
			for form in ipform:
				ipaddr = form.cleaned_data.get('ipaddr')
				vendor = form.cleaned_data.get('vendor')
				print (vendor)
				ssh_client = paramiko.SSHClient()
				ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				ssh_client.connect(hostname=ipaddr,port=5555,username=userValue,password=passValue)
				remote_conn=ssh_client.invoke_shell()
				output = remote_conn.recv(65535)
				stdin,stdout,stderr = ssh_client.exec_command(confValue)
				time.sleep(3)
				print (output)
				print (stdout.read())
				simpanIp = form.save(commit=False)
				simpanIp.connect_id = simpanForm
				print (simpanIp)
				simpanIp.save()

			simpanForm.save()

		return HttpResponseRedirect('config/vlan')
	def get(self, request, *args, **kwargs):
		formm = NacmForm()
		ipform = IpFormset()
		return render(request, 'config/vlan.html', {'form': formm, 'logins': Connect.objects.all(), 'ipform': ipform, 'status': self.status })

class backup(View):
	ip_list = []
	backup_dir = "/backup/"
	now = datetime.datetime.now()
	file_download = "%s_%.2i-%.2i-%i" % ('conf_backup',now.day,now.month,now.year)
	file_name = "%s" % ('conf_backup')
	def post(self, request, *args, **kwargs):
		formm = NacmForm(request.POST or None)
		ipform = IpFormset(request.POST)
		userValue = formm['username'].value()
		passValue = formm['password'].value()
		confValue = formm['conft'].value()

		if ipform.is_valid():
			for form in ipform:
				ipaddr = form.cleaned_data.get('ipaddr')
				vendor = form.cleaned_data.get('vendor')
				filename_prefix = ipaddr+'.cfg'
				filename_complete = os.path.join(self.backup_dir, filename_prefix)
				print ("true")
				# print ipaddr
				ssh_client = paramiko.SSHClient()
				ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				ssh_client.connect(hostname=ipaddr,username=userValue,password=passValue)

				if request.POST.get("backup"):
					if not os.path.exists(self.backup_dir):
						os.makedirs(self.backup_dir)

					file_paths = get_all_file_paths(self.backup_dir)
					# stdin, stdout, stderr = ssh_client.exec_command('/export')
					# stdin, stdout, stderr = ssh_client.exec_command('show run')
					stdin, stdout, stderr = ssh_client.exec_command(eval(vendor.sett_backup))
					backup = stdout.read()

					filename = "%s" % (filename_complete)
					ff = open(filename, 'wb')
					ff.write(backup)
					ff.close()
					value_bak="zipping_file"

			if value_bak=="zipping_file":
				# try:
				s=BytesIO()
				zf = zipfile.ZipFile(s, 'w')
				zipper = shutil.make_archive(self.file_name, 'zip', self.backup_dir)
				print(zipper)
				shutil.rmtree(self.backup_dir)
				resp = HttpResponse(open(zipper, 'rb'), content_type = 'application/x-zip-compressed')
				# ..and correct content-disposition
				resp['Set-Cookie'] = ('fileDownload=true; Path=/')
				resp['Content-Disposition'] = 'attachment; filename=%s' % self.file_download+".zip"
				print(resp)
				del_dir = os.getcwd()
				os.remove(del_dir+'/'+self.file_name+'.zip')
				formm.save()
				return resp
				# finally:
				# 	print('aye')
				# 	return redirect('/backup')
				# formm.save()
		# 	elif request.POST['action'] == 'Download': 
        # # return(HttpResponseRedirect('/App/download'))
		# 		return HttpResponseRedirect('/backup')

	def get(self, request, *args, **kwargs):
		formm = NacmForm()
		ipform = IpFormset()
		file_download = "%s_%.2i-%.2i-%i.zip" % ('conf_backup',self.now.day,self.now.month,self.now.year)
		return render(request, 'backup.html', {'form': formm, 'logins': Connect.objects.all(), 'ipform': ipform, 'file_download':file_download})

	# def zipfile():
	# 	zipper = shutil.make_archive(self.file_name, 'zip', self.backup_dir)
	# 	print(zipper)
	# 	shutil.rmtree(self.backup_dir)
	# 	resp = HttpResponse(open(zipper, 'rb'), content_type = 'application/zip')
	# 	# ..and correct content-disposition
	# 	resp['Content-Disposition'] = 'attachment; filename=%s' % self.file_download+".zip"
	# 	print(resp)
	# 	del_dir = os.getcwd()
	# 	os.remove(del_dir+'/'+self.file_name+'.zip')
	# 	return resp	

class restore(View):
	ip_list = []

	def post(self, request, *args, **kwargs):
		formm = NacmForm(request.POST or None)
		ipform = IpFormset(request.POST)
		upform = UploadForm(request.POST,request.FILES)
		userValue = formm['username'].value()
		passValue = formm['password'].value()

		if ipform.is_valid():
			for form in ipform:
				ipaddr = form.cleaned_data.get('ipaddr')
				print ("true")
				ssh_client = paramiko.SSHClient()
				ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				ssh_client.load_system_host_keys()
				ssh_client.connect(hostname=ipaddr,username=userValue,password=passValue)
				if request.POST.get("upload"):
					localfilepath = os.getcwd()
					remotefilepath = 'auto.cfg'
					print('test wanna upload something....')
					mediapath = localfilepath+'/media/'
					for count, x in enumerate(request.FILES.getlist("files")):
						def process(f):
							with open( localfilepath + '/media/' + f.name, 'wb+') as destination:
								for chunk in f.chunks():
									destination.write(chunk)

							def files(mediapath):
								for file in os.listdir(mediapath):
									if os.path.isfile(os.path.join(mediapath, file)):
										files = file.rsplit('.',1)[0]
										yield files

							for ftp_con in files(mediapath):
								print (ftp_con)
								ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
								ssh_client.load_system_host_keys()
								ssh_client.connect(hostname=ftp_con,username=userValue,password=passValue)
								print("upload")
								scp = SCPClient(ssh_client.get_transport())
								scp.put(mediapath + ftp_con+'.cfg', ftp_con+'.cfg')
								scp.close()
								os.remove(mediapath+ftp_con+'.cfg')
						process(x)

					time.sleep(10)
					return HttpResponseRedirect('/restore')
				formm.save()

			return HttpResponseRedirect('/restore')
	def get(self, request, *args, **kwargs):
		formm = NacmForm()
		ipform = IpFormset()
		upform = UploadForm()
		return render(request, 'restore.html', {'form': formm, 'logins': Connect.objects.all(), 'ipform': ipform, 'upform': upform })

def Settings_display(request):

	settForm = SettingForm()
	return render(request, 'setting/display.html', {'settings': settings.objects.all(), 'form': settForm })

def Settings_add(request):
	if request.method == 'POST':
		settForm = SettingForm(request.POST)
	
		if settForm.is_valid():
			settForm.save()

		return HttpResponseRedirect('/setting')
	
	else:
		settForm = SettingForm()
		return render(request, 'setting/add.html', {'settings': settings.objects.all(), 'form': settForm })

def Settings_edit(request, pk):
	setting = get_object_or_404(settings, pk=pk)
	status = 'success'
	nameValue = settings.objects.filter(pk=pk).values('sett_name')[0];
	name = nameValue['sett_name']

	if request.method == 'POST':
		post_form = SettingForm(request.POST, instance=setting)
		if post_form.is_valid():
			post_form.save()
		return HttpResponseRedirect('/setting')
	else:
		form = SettingForm(instance=setting)
		return render(request, 'setting/edit.html', {'form': form, 'name': name, 'status': status })

def Settings_delete(request, pk):
    settingdel = settings.objects.get(pk=pk)
    settingdel.delete()
    return HttpResponseRedirect('/setting')

def verifip(request):
	print ("verifikasi ip")

def ip_validation(request):
	# ipform = IpFormset(request.POST)
	if request.method == 'POST':
		if request.is_ajax():
			ip_list_json = request.POST.get('iplist')
			ok_ip_list = []
			print (ip_list_json)
			print ("Checking the connection.....")
			response = os.system("ping" + ip_list_json)
			respon_koneksi = " "
			if response == 0 :
				respon_koneksi = ip_list_json+" is connected"
				# print respon_koneksi
			else:
				respon_koneksi = ip_list_json+" is not connected"

			print (respon_koneksi)
			data = {'respon_koneksi': respon_koneksi}
			return HttpResponse(
				json.dumps(data)
			)
	else:
		passes = "nothing"
		return HttpResponse(content_type="application/json")

def history(request):
	formm = NacmForm()
	ipform = IpFormset()
	return render(request, 'log.html', {'form': formm, 'logins': Connect.objects.all(), 'ipform': ipform})



def get_all_file_paths(directory):

    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    # returning all file paths
    return file_paths

class LoginInfo(generics.ListCreateAPIView):
	queryset = models.Connect.objects.all()
	serializer_class = serializers.AutonetSerializer

class LoginInfoDetail(generics.RetrieveUpdateDestroyAPIView):
	queryset = models.Connect.objects.all()
	serializer_class = serializers.AutonetSerializer

class IpInfo(generics.ListCreateAPIView):
	queryset = models.Ip.objects.all()
	serializer_class = serializers.IpAutonetSerializer

class IpInfoDetail(generics.RetrieveUpdateDestroyAPIView):
	queryset = models.Ip.objects.all()
	serializer_class = serializers.IpAutonetSerializer

class DataInfo(generics.ListCreateAPIView):
	queryset = models.Connect.objects.all()
	serializer_class = serializers.DataAutonetSerializer
