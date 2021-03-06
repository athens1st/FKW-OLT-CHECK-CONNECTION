import paramiko
import os, os.path, time, socket
import re
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.views import View
from ..models import Connect
from ..forms import NacmForm, IpFormset
from .. import models
from netaddr import IPAddress, IPNetwork

class vlan(View):
	ip_list = []
	
	# hal yang dilakukan ketika melakukan action POST	
	def post(self, request, *args, **kwargs):
		# mengambil nilai dari form
		formm = NacmForm(request.POST or None)
		ipform = IpFormset(request.POST)
		userValue = formm['username'].value()
		passValue = formm['password'].value()
		confValue = formm['conft'].value()

		# jika form valid
		if ipform.is_valid() and formm.is_valid():
			count_form = 0
			collect_data = ""
			simpanForm = formm.save()

			# perulangan data pada form ipform
			for form in ipform:
				ipaddr = form.cleaned_data.get('ipaddr')
				vendor = form.cleaned_data.get('vendor')
				dba_profiles = (request.POST.getlist('dba_profile'))
				mode_dba_profiles = (request.POST.getlist('mode_dba_profile'))
				sla_fixeds = (request.POST.getlist('sla_fixed'))
				sla_assureds = (request.POST.getlist('sla_assured'))
				sla_maximums = (request.POST.getlist('sla_maximum'))
				
				# vlans_id = (request.POST.getlist('vlan_id'))
				# vlans_name = (request.POST.getlist('vlan_name'))
				# interface = str(request.POST['interface'])
				collect_config = "<b>Configure on "+str(ipaddr)+" | vendor = "+str(vendor)+"</b></br>"
				print (vendor)
				
				# mengkoneksikan ke perangkat via protokol SSH menggunakan library Paramiko
				try:
					ssh_client = paramiko.SSHClient()
					ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
					# memasukkan informasi username, password SSH
					ssh_client.connect(hostname=ipaddr,port=5555,username=userValue,password=passValue,look_for_keys=False, allow_agent=False, timeout=5)
					remote_conn=ssh_client.invoke_shell()
					shell = remote_conn.recv(65535)
					config_read = str(vendor.sett_vlan)
					# split memakai \r dulu
					array_read = config_read.split('\r')
					# hasilnya akan ada \n
					output_line = ""

					# membuat perulangan pada vlan id dan vlan name yang ditambahkan, karena pada vlan id dan vlan name menggunakan form dinamis
					for x in range(len(dba_profiles)):
						dba_profile = dba_profiles[x]
						mode_dba_profile = mode_dba_profiles[x]
						sla_fixed = sla_fixeds[x]
						sla_assured = sla_assureds[x]
						sla_maximum = sla_maximums[x]

					# for x in range(len(vlans_id)):
					# 	vlan_id = vlans_id[x]
					# 	vlan_name = vlans_name[x]

						# membaca code tiap line
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
								# mengirim perintah yang akan dikonfig
								# menggunakan non-interactive shell
								try:
									stdin, stdout, stderr = ssh_client.exec_command(config_send+"\n")
									time.sleep(3)
									results = stdout.read()
									print (str(results))
								except:
									# jika gagal menggunakan interactive shell
									try:
										remote_conn.send(config_send+"\n")
										time.sleep(3)
										results = remote_conn.recv(65535)
										print (results.decode('ascii'))
									except:
										print("error paramiko")

					# menyimpan data ke sqlite
					messages.success(request, collect_config)
					count_form = count_form + 1	
					collect_data = collect_data + collect_config
					if count_form == len(ipform):
						simpanForm.conft = collect_data
					simpanIp = form.save(commit=False)
					simpanIp.connect_id = simpanForm
					print (simpanIp)
					simpanIp.save()
					simpanForm.save()

				# jika gagal terkoneksi
				except paramiko.AuthenticationException:
					error_conf(request, collect_config, "</br>Authentication failed, please verify your credentials")
				except paramiko.SSHException as sshException:
					error_conf(request, collect_config, "</br>Could not establish SSH connection: %s" % sshException)
				except socket.timeout as e:
					error_conf(request, collect_config, "</br>Connection timed out")
				except Exception as e:
					ssh_client.close()
					error_conf(request, collect_config, "</br>Exception in connecting to the server")

		return HttpResponseRedirect('vlan')

	# hal yang dilakukan ketika melakukan action GET
	def get(self, request, *args, **kwargs):
		formm = NacmForm()
		ipform = IpFormset()
		return render(request, 'config/vlan.html', {'form': formm, 'logins': Connect.objects.all(), 'ipform': ipform })

def error_conf(request, collect_config, error1):
	conf_error = collect_config+error1
	messages.error(request, conf_error)
	result_flag = False