from django.http import HttpResponseRedirect, HttpResponse, HttpResponsePermanentRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.utils.encoding import smart_str

from rdatkit import SecondaryStructure

from src.env import error400, error401, error403, error404, error500, error503
from src.models import *
from src.settings import *

# from src.helper.helpers import *
# from src.helper.helper_api import *
# from src.helper.helper_predict import *

from src.util.entry import *
from src.util.media import *
from src.util.stats import *
from src.util.util import *

from datetime import datetime
import simplejson
# import traceback

dist_dict = {'mapseeker': 'MAPseeker', 'reeffit': 'REEFFIT', 'hitrace': 'HiTRACE', 'rdatkit': 'RDATKit', 'biers': 'Biers'}


def index(request):
    return render(request, PATH.HTML_PATH['index'])

def browse(request):
    return render(request, PATH.HTML_PATH['browse'])

def specs(request):
    return render(request, PATH.HTML_PATH['specs'])

def tools(request):
    return render(request, PATH.HTML_PATH['repos'])

def tools_license(request, keyword):
    if keyword in dist_dict:
        title = dist_dict[keyword]
        file_name = '%s/dist/%s-LICENSE.md' % (MEDIA_ROOT, title)
        license_md = '404 Not Found'
        if os.path.exists(file_name):
            license_md = ''.join(open(file_name, 'r').readlines())
            license_md = license_md.replace('\n', '<br/>') + '</strong>'

        return render(request, PATH.HTML_PATH['tools_license'], {'keyword': keyword, 'title': title, 'license_md': license_md})
    else:
        return error404(request)

@login_required
def tools_download(request, keyword):
    if keyword in dist_dict:
        new = SourceDownloader(date=datetime.now(), package=keyword, rmdb_user=RMDBUser.objects.get(user=request.user))
        new.save()

        result = simplejson.load(open('%s/cache/stat_dist.json' % MEDIA_ROOT, 'r'))
        result = result[keyword]
        title = dist_dict[keyword]
        return render(request, PATH.HTML_PATH['tools_download'], {'keyword': keyword, 'title': title, 'dist': result})
    else:
        return error404(request)

@login_required
def tools_link(request, keyword, tag):
    records = SourceDownloader.objects.filter(package=keyword, rmdb_user=RMDBUser.objects.get(user=request.user))
    if len(records):
        title = dist_dict[keyword]
        tag = tag.replace('/', '')
        file_name = '%s/dist/%s-%s.zip' % (MEDIA_ROOT, title, tag)
        if os.path.exists(file_name):
            response = HttpResponse(content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=%s-%s.zip' % (title, tag)
            response['X-Sendfile'] = smart_str(file_name)
            return response
        else:
            return error404(request)
    return error401(request)

def tutorial(request, keyword):
    if keyword in dist_dict:
        return HttpResponsePermanentRedirect('https://ribokit.github.io/' + dist_dict[keyword])
    elif keyword in ('predict', 'api'):
        return render(request, PATH.HTML_PATH['tutorial'].replace('xxx', keyword), {})
    else:
        return error404(request)

def about(request):
    return render(request, PATH.HTML_PATH['about'])

def license(request):
    return render(request, PATH.HTML_PATH['license'])

def history(request):
    return render(request, PATH.HTML_PATH['history'], {'hist': parse_history()})


def detail(request, rmdb_id):
    try:
        entry = RMDBEntry.objects.filter(rmdb_id=rmdb_id).order_by('-version')[0]
        is_isatab = os.path.exists('%s%s/%s_%s.xls' % (PATH.DATA_DIR['FILE_DIR'], entry.rmdb_id, entry.rmdb_id, entry.version))
    except (RMDBEntry.DoesNotExist, IndexError):
        return error404(request)

    json = {'rmdb_id': entry.rmdb_id, 'status': entry.status, 'is_isatab': is_isatab}
    if entry.status != "PUB":
        json.update({'version': entry.version, 'rev_form': ReviewForm(initial={'rmdb_id': entry.rmdb_id})})
    return render(request, PATH.HTML_PATH['detail'], json)


def predict(request):
    # if request.method != 'POST':
    return render(request, PATH.HTML_PATH['predict'], {'secstr_form': PredictionForm(), 'rdatloaded': False, 'messages': [], 'other_errors': []})
    # else:
    #     try:
    #         sequences, titles, structures, modifiers, mapping_data, base_annotations, messages, valerrors = ([],[],[],[],[],[],[],[])

    #         is_get_rmdb = (len(request.POST['rmdbid']) > 0)
    #         is_get_file = (len(request.POST['rdatfile']) > 0)
    #         if is_get_rmdb or is_get_file:
    #             (messages, valerrors, bonuses_1d, bonuses_2d, titles, modifiers, offset_seqpos, temperature, sequences, refstruct) = parse_rdat_data(request, is_get_file)
    #             form = fill_predict_form(request, sequences, structures, temperature, refstruct, bonuses_1d, bonuses_2d, modifiers, titles, offset_seqpos)
    #             return render(request, PATH.HTML_PATH['predict'], {'secstr_form': form, 'rdatloaded': True, 'msg_y': messages, 'msg_r': valerrors})
    #         elif not request.POST['sequences']:
    #             return render(request, PATH.HTML_PATH['predict'], {'secstr_form': PredictionForm(), 'rdatloaded': False, 'msg_y': [], 'msg_r': []})

    #         other_options = ' -t %s ' % (float(request.POST['temperature']) + 273.15)
    #         refstruct = SecondaryStructure(dbn=request.POST['refstruct'])

    #         lines = request.POST['sequences'].split('\n')
    #         for l in lines:
    #             if l:
    #                 if l[0] == '>':
    #                     titles.append(l.replace('>',''))
    #                 else:
    #                     if l.strip():
    #                         sequences.append(rna.RNA(l.strip()))
    #         if not sequences:
    #             messages.append('ERROR: No SEQUENCE found. Due to either no input field, or no modification lanes in RDAT.')
    #             return render(request, PATH.HTML_PATH['predict_res'], {'panels': [], 'messages': messages,'bppmimg': '', 'ncols': 0, 'nrows': 0})

    #         if 'structures' in request.POST:
    #             lines = request.POST['structures'].split('\n')
    #             for l in lines:
    #                 if l.strip():
    #                     structures.append(l)

    #         if request.POST['predtype'] in ('NN', '1D'):
    #             (base_annotations, structures, mapping_data, messages) = predict_run_1D_NN(request, sequences, mapping_data, structures, other_options, messages)

    #         if request.POST['predtype'] == '2D':
    #             (sequences, structures, messages, base_annotations) = predict_run_2D(request, sequences, titles, structures, other_options, messages)
    #             modifiers = ['']


    #         panels, ncols, nrows = render_to_varna([s.sequence for s in sequences], structures, modifiers, titles, mapping_data, base_annotations, refstruct)
    #         visform_params = {}
    #         visform_params['sequences'] = '\n'.join([s.sequence for s in sequences])
    #         visform_params['structures'] = '\n'.join([s.dbn for s in structures])
    #         if 'raw_bonuses' in request.POST:
    #             print [str(slope*log(1 + d) + intercept) for d in mapping_data[0].data()]
    #             visform_params['md_datas'] = '\n'.join([','.join([str(slope*log(1 + d) + intercept) for d in m.data()]) for m in mapping_data])
    #         else:
    #             visform_params['md_datas'] = '\n'.join([','.join([str(d) for d in m.data()]) for m in mapping_data])
    #         visform_params['md_seqposes'] = '\n'.join([','.join([str(pos) for pos in m.seqpos]) for m in mapping_data])
    #         visform_params['modifiers'] = modifiers
    #         visform_params['base_annotations'] = '\n'.join([bpdict_to_str(ann) for ann in base_annotations])
    #         visform_params['refstruct'] = refstruct.dbn
    #         visform = VisualizerForm(visform_params)
    #         return render(request, PATH.HTML_PATH['predict_res'], {'panels': [], 'messages': messages,'ncols': [], 'nrows': [], 'form': visform})

    #     except IndexError, err:
    #         print err
            # return render(request, PATH.HTML_PATH['predict'], {'secstr_form': PredictionForm(), 'rdatloaded': False, 'msg_y': messages, 'msg_r': ['Invalid input. Please check your inputs and try again.']})


def str_view(request):
    return render(request, PATH.HTML_PATH['index'])


def search(request):
    if request.method == 'POST':
        return error400(request)
    else:
        form = SearchForm(request.GET)
        if form.is_valid():
            sstring = form.cleaned_data['sstring'].encode('utf-8', 'ignore')
            return render(request, PATH.HTML_PATH['search_res'], {'sstring': sstring})
        else:
            return render(request, PATH.HTML_PATH['search_res'], {'sstring': ''})


def advanced_search(request):
    return error503(request)


def validate(request):
    flag = -1
    if request.method == 'POST':
        form = ValidateForm(request.POST, request.FILES)
        if form.is_valid():
            link = form.cleaned_data['link']
            upload_file = '' if link else request.FILES['file']
            (errors, messages, flag) = validate_file(upload_file, link, form.cleaned_data['file_type'])

    if flag == -1:
        (messages, errors, flag, form) = ([], [], 0, ValidateForm())
    return render(request, PATH.HTML_PATH['validate'], {'form': form, 'val_errs': errors, 'val_msgs': messages, 'flag': flag})


@login_required
def upload(request):
    flag = 0
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload_file = request.FILES['file']
            user = request.user
            (error_msg, flag, entry) = process_upload(form, upload_file, user)

            if os.path.exists('%s/%s' % (PATH.DATA_DIR['TMP_DIR'], upload_file.name)):
                os.remove('%s/%s' % (PATH.DATA_DIR['TMP_DIR'], upload_file.name))
        else:
            flag = 1
            (error_msg, entry) = ([], '')
            if 'rmdb_id' in form.errors: error_msg.append('RMDB_ID field is required.')
            if 'file' in form.errors: error_msg.append('Input file field is required.')
            if 'authors' in form.errors: error_msg.append('Authors field is required.')

    if not flag:
        (error_msg, flag, entry, form) = ([], 0, '', UploadForm())
    return render(request, PATH.HTML_PATH['upload'], {'form': form, 'error_msg': error_msg, 'flag': flag, 'entry': entry})


@user_passes_test(lambda u: u.is_superuser)
def review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            new_stat = form.cleaned_data['new_stat']
            rmdb_id = form.cleaned_data['rmdb_id']
            review_entry(new_stat, rmdb_id)

            return HttpResponseRedirect('/detail/%s' % rmdb_id)

    return error400(request)


def get_admin(request):
    return HttpResponse(simplejson.dumps({'email': EMAIL_NOTIFY}, sort_keys=True, indent=' ' * 4), content_type='application/json')

def get_user(request):
    if request.user.username:
        user = request.user.username
    else:
        user = 'unknown'
    return HttpResponse(simplejson.dumps({'user': user}, sort_keys=True, indent=' ' * 4), content_type='application/json')

def get_js(request):
    stats = simplejson.load(open('%s/cache/stat_ver.json' % MEDIA_ROOT, 'r'))
    json = {'jquery': stats['jquery'], 'bootstrap': stats['bootstrap'], 'd3': stats['d3']}
    return HttpResponse(simplejson.dumps(json, sort_keys=True, indent=' ' * 4), content_type='application/json')


def get_stats(request):
    json = do_get_stats()
    if json is None: return error503(request)

    for key in json.keys():
        json[key] = '{:,}'.format(json[key])
    return HttpResponse(simplejson.dumps(json, sort_keys=True, indent=' ' * 4), content_type='application/json')

def get_news(request):
    n_news = 12
    news = NewsItem.objects.all().order_by('-date')[:n_news]
    json = {}
    for i, n in enumerate(news):
        json[i] = {'content': n.content, 'date': n.date.strftime('%b %d, %Y')}
    return HttpResponse(simplejson.dumps(json, sort_keys=True, indent=' ' * 4), content_type='application/json')

def get_recent(request):
    entries = RMDBEntry.objects.all().filter(status='PUB').order_by('-creation_date')
    entries_list = []
    for e in entries:
        if e.rmdb_id not in entries_list:
            entries_list.append(e.rmdb_id)
        if len(entries_list) == 10:
            break
    entries = []
    for e in entries_list:
        entries.append(RMDBEntry.objects.filter(rmdb_id=e).order_by('-creation_date')[0])

    entries_list = []
    for e in entries:
        for c in ConstructSection.objects.filter(entry=e).values('name').distinct():
            name = c['name']
        e_temp = {'name': name, 'rmdb_id': e.rmdb_id}
        entries_list.append(e_temp)
    return HttpResponse(simplejson.dumps(entries_list, sort_keys=True, indent=' ' * 4), content_type='application/json')

def get_browse(request, keyword):
    if keyword in ('general', 'puzzle', 'eterna'):
        json = simplejson.load(open('%s/cache/stat_browse_%s.json' % (MEDIA_ROOT, keyword), 'r'))
        return HttpResponse(simplejson.dumps(json, sort_keys=True, indent=' ' * 4), content_type='application/json')
    else:
        return error400(request)


def ping_test(request):
    return HttpResponse(content="", status=200)


def test(request):
    # entry = RMDBEntry.objects.all()[0]
    # send_notify_emails(entry, 'tinecidy627@gmail.com')

    raise ValueError
    return HttpResponse(content="", status=200)


