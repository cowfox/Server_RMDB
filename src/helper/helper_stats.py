from src.models import *
from src.settings import *

import glob
import textwrap
import time


def get_rmdb_stats():
	rmdb_ids = [d.values()[0] for d in RMDBEntry.objects.values('rmdb_id').distinct()]
	N_all = 0
	N_RNA = 0
	# N_RNA = ConstructSection.objects.values('name').distinct().count()
	N_puzzle = 0
	N_eterna = 0
	N_constructs = 0
	N_datapoints = 0
	for rmdb_id in rmdb_ids:
		entries = RMDBEntry.objects.filter(rmdb_id=rmdb_id).order_by('-version')
		if len(entries) >= 0:
			N_all += 1
			N_RNA += len(entries)

			if 'RNAPZ' in rmdb_id:
				N_puzzle += 1
			if 'ETERNA' in rmdb_id:
				N_eterna += 1
			e = entries[0]
		N_datapoints += e.data_count
		N_constructs += e.construct_count		
	return (N_all, N_RNA, N_puzzle, N_eterna, N_constructs, N_datapoints)


def browse_json_list(names_d):
	constructs = []
	for c in names_d:
		entries = RMDBEntry.objects.filter(constructsection__name=c['name']).filter(revision_status='PUB').order_by( 'rmdb_id', '-version' )
		entry_ids = []
		SS_entries, MA_entries, MM_entries, TT_entries = [], [], [], []

		for e in entries:
			if e.rmdb_id not in entry_ids:
				entry_ids.append(e.rmdb_id)
				e.cid = ConstructSection.objects.filter( entry = e ).values( 'id' )[ 0 ][ 'id' ]
				comment = e.comments.split()
				for i, m in enumerate(comment):
					if len(m) > 40:
						comment[i] = ' '.join(textwrap.wrap(m, 40))
				entry = {'rmdb_id':e.rmdb_id, 'cid':e.cid, 'version':e.version, 'construct_count':e.constructcount, 'data_count':e.datacount, 'authors':e.authors, 'comments':' '.join(comment), 'title':e.publication.title, 'latest':e.latest}
				if e.type == "SS":
					SS_entries.append(entry)
				elif e.type == "MM":
					MM_entries.append(entry)
				elif e.type == "MA":
					MA_entries.append(entry)
				elif e.type == "TT":
					TT_entries.append(entry)

		constructs.append({'name':c['name'], 'SS_entry':SS_entries, 'MM_entry':MM_entries, 'MA_entry':MA_entries, 'TT_entry':TT_entries})
	return constructs


class BrowseResults:
	pass


def get_rmdb_category(flag):
	if flag == "puzzle":
		names_d = ConstructSection.objects.filter(name__icontains='Puzzle').values('name').distinct()
	elif flag =="eterna":
		names_d = ConstructSection.objects.filter(name__icontains='EteRNA').values('name').distinct()
	else:
		names_d = ConstructSection.objects.exclude(name__icontains='EteRNA').exclude(name__icontains='Puzzle').values('name').distinct()
	names_d = names_d.order_by( 'name' )
	return browse_json_list(names_d)


def get_history():
	file_list = glob.glob(MEDIA_ROOT + "/misc/log_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].txt")
	file_list.sort()
	log_content = []

	for log_file in file_list:
		f = open(log_file, 'r')
		lines = [line for line in f.readlines() if line.strip()]
		f.close()

		ls_1_flag = 0
		ls_2_flag = 0
		for i in range(len(lines)):
			lines[i] = lines[i].rstrip()
			if lines[i][0] == "#":
				lines[i] = "<span class=\"lead\"><b>" + lines[i][1:] + "</b></span><br/>"
			elif lines[i][0] != '-':
				if lines[i][0] == "!":
					lines[i] = "by <kbd><i>" + lines[i][1:] + "</i></kbd><br/><br/>"
				else:
					lines[i] = "<p>" + lines[i] + "</p><p><ul>"
				
			else:
				if lines[i][:2] != '-\\':
					lines[i] = "<li><u>" + lines[i][1:] + "</u></li>"
					if ls_1_flag:
						lines[i] = "</ul></p>" + lines[i]
					ls_1_flag = i

				else:
					lines[i] = "<li>" + lines[i][2:] + "</li>"
					if ls_2_flag < ls_1_flag:
						lines[i] = "<ul><p>" + lines[i]
					ls_2_flag = i

		lines.append("</ul></ul><br/><hr/>")
		date_string = log_file[log_file.find("log_")+4 :-4]
		date_string = time.strftime("%b %d, %Y (%a)", time.strptime(date_string, "%Y%m%d"))
		lines.insert(0, "<i>%s</i><br/>" % date_string)
		log_content.insert(0, "".join(lines))

	return "".join(log_content)