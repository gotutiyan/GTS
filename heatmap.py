def generate_heatmap_combine(gold_chunks, file_name):
    number_of_systems = -1
    head = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" type="text/css" href="./"""+file_name.split('/')[-1]+""".css">
        <title>heat-map</title>
    </head>
    <script type="text/javascript">
        function f(message){
            document.getElementById("explanation").innerText=message;
        }
    </script>
    <body>
    <div style="position: fixed; left:0;top:0;background-color:rgb(180,180,180); padding:1px;">
        <p id="explanation" style="font-weight:900;">Mouseover to show information about corrections . </p>
    </div>
    <div style="margin:70px 0px 0px 0px">
    """
    foot = """
    </div>
    </body>
    </html>
    """
    out_fp = open(file_name,"w")
    out_fp.write(head)
    for sent, systems in gold_chunks.items():
        sent = sent.split()
        s = "<p>"
        for gchunk in systems[0]:
            number_of_systems = max(len(gchunk.sys2eval), number_of_systems)
            s += convert_chunk_to_htmlsentence(gchunk, sent)
        s += "</p>"
        out_fp.write(s+"\n")
    out_fp.write(foot)
    generate_css(number_of_systems, file_name)
    out_fp.close()

def convert_chunk_to_htmlsentence(gchunk, sent):
    s = ''
    mouseover = 'onmouseover="f({})"'.format("'[error type]: "+\
                                        gchunk.cat+' [correct]: '+\
                                        gchunk.gold_sent+\
                                        ' [weight]: '+\
                                        str(round(gchunk.weight,2))+" '")
    # BASIC chunk
    if gchunk.orig_range[0] != gchunk.orig_range[1]:
        if not gchunk.is_error:
            if count_false_positive(gchunk) > 0:
                s += '<span class="bluew'+str(round(gchunk.weight*100))+'" '+mouseover+'>'+\
                     ' '.join(sent[gchunk.orig_range[0]:gchunk.orig_range[1]])+'</span> '
            else:
                s += ' '.join(sent[gchunk.orig_range[0]:gchunk.orig_range[1]])
        else:
            s += '<span class="redw'+str(round(gchunk.weight*100))+'" '+mouseover+'>'+\
                 ' '.join(sent[gchunk.orig_range[0]:gchunk.orig_range[1]])+'</span> '
    # INSERT chunk
    else:
        if gchunk.is_error:
            s += '<span class="redw'+str(round(gchunk.weight*100))+'" '+mouseover+'>'+' '+'</span> '
        else:
            if count_false_positive(gchunk) > 0:
                s += '<span class="bluew'+str(round(gchunk.weight*100))+'" '+mouseover+'>'+' '+'</span> '
            else:
                s+=' '
    return s

def count_false_positive(chunk):
    ret = 0
    for evalinfo in chunk.sys2eval.values():
        if evalinfo.is_modify and not evalinfo.is_correct:
            ret += 1
    return ret

def generate_css(number_of_systems, file_name):
    file_name += '.css'
    out_fp = open(file_name,"w")
    delta = 1 / number_of_systems
    s = ''
    color = dict()
    color['red'] = '255,0,0,'
    color['blue'] = '0,0,255,'
    
    for i in range(number_of_systems + 1):
        if delta*i <0.7: s = '.redw'+str(round(delta*i*100))+'{ background-color: rgb('+color['red']+str(min(1.0, max(delta*i, 0.1)))+')}'
        else: s = '.redw'+str(round(delta*i*100))+'{ background-color: rgb('+color['red']+str(min(1.0, max(delta*i, 0.1)))+');font-weight:900;}'
        out_fp.write(s+'\n')
    for i in range(number_of_systems + 1):
        if delta*i <0.7: s = '.bluew'+str(round(delta*i*100))+'{ background-color: rgb('+color['blue']+str(min(1.0, max(delta*i, 0.1)))+')}'
        else: s = '.bluew'+str(round(delta*i*100))+'{ background-color: rgb('+color['blue']+str(min(1.0, max(delta*i, 0.1)))+');font-weight:900;}'
        out_fp.write(s+'\n')
    out_fp.close()