from flask import Blueprint
from flask import Flask, render_template, request, redirect, url_for, send_file, flash

#from api.compute import compute

import uuid
import json
import os
import re
import shutil

personal = Blueprint('personal', __name__, template_folder='templates')

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)

@personal.route('/')
def index():
    return render_template('home.html')

@personal.route('/graph')
def graph():
    df = pd.read_csv('Advertising.csv', index_col=0)
    df.sort_values(['Sales'], inplace=True)
    fig = go.Figure()
    for cname in df.columns[:-1]:
        fig.add_scatter(x=df[cname], y=df['Sales'], name=cname, mode="markers")

    fig.update_layout(width=1600, height=800)
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('graph.html',
                           ids='invest',
                           graphJSON=graphJSON)


@personal.route('/table')
def table():
    df = pd.read_csv('Advertising.csv', index_col=0)

    #meas = [dffinal.iloc[i].to_dict() for i in range(dffinal.shape[0])]
    meas = [list(map(str, df.iloc[i].values)) for i in range(df.shape[0])]
    #meas = {'data': meas}
    ddffinal = json.dumps(meas, cls=NpEncoder)
    return render_template('table.html',
                           dffinal=ddffinal)

@personal.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        f = request.files.get('file')
        filename = f'{str(uuid.uuid4())}_{f.filename}'
        f.save(os.path.join('api/static/uploads', filename))
    return render_template('upload.html')

@personal.route('/analysis', methods=['POST', 'GET'])
def analysis():
    options = os.listdir('api/static/uploads')
    error = None
    if request.method == 'POST':
        form_dict = dict(request.form)
        data_list = request.form.getlist('category')
        #print(form_dict)
        #print(data_list)
        if form_dict['remove']=='sim':
            if len(data_list):
                for fn in data_list:
                    os.remove(os.path.join('api/static/uploads', fn))
            return redirect(url_for('personal.analysis'))
        try:
            compute(form_dict, data_list, str(uuid.uuid4()))
        except Exception as e:
            #print(e)
            return render_template('analysis.html', options=options,
                                   error=str(e))
        return redirect(url_for('personal.results'))
    return render_template('analysis.html', options=options, error=error)


@personal.route('/results')
def results():
    fls = os.listdir('api/static/results')
    meas = [x.split('###') for x in fls]
    for i in range(len(meas)):
        tmp = meas[i]+[]
        url = '/static/results/%s' % '###'.join(tmp)
        #link = f'<a href="{url}" target="_blank">File</a>'
        link = url
        tmp = [re.sub('.tsv$|.pdf$|.gml$', '', x) for x in tmp]
        tmp.append(link)
        meas[i] = tmp
    ddffinal = json.dumps(meas, cls=NpEncoder)
    return render_template('results.html',
                           dffinal=ddffinal)


@personal.route('/download')
def download():
    taskid = request.args.get('taskid')
    dr = os.path.join('api/static/results')
    fls = os.listdir(dr)
    fls = [x for x in fls if taskid in x][0]
    fls = 'static/results/%s' % fls
    return send_file(fls, as_attachment=True)

@personal.route('/delete')
def delete():
    taskid = request.args.get('taskid')
    dr = os.path.join('api/static/results')
    fls = os.listdir(dr)
    fls = [x for x in fls if taskid in x][0]
    fls = 'api/static/results/%s' % fls
    if os.path.isfile(fls):
        os.unlink(fls)
    else:
        shutil.rmtree(fls)
    return redirect(url_for('personal.results'))

