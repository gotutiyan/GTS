def generate_heatmap(gold_chunks: list, file_name: str) -> None:
    number_of_systems = len(gold_chunks[0][0].sys2eval)
    css_str = generate_css(number_of_systems)
    head = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>heat-map</title>
    """ + css_str + """
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
    out_fp = open(file_name, "w")
    out_fp.write(head)
    for gold_chunk in gold_chunks:
        s = "<p>"
        for gchunk in gold_chunk:
            number_of_systems = max(len(gchunk.sys2eval), number_of_systems)
            s += convert_chunk_to_htmlsentence(gchunk)
        s += "</p>"
        out_fp.write(s+"\n")
    out_fp.write(foot)
    out_fp.close()
    return


def convert_chunk_to_htmlsentence(gchunk) -> list:
    s = ''
    mouseover = 'onmouseover="f({})"'.format(
        "'[error type]: "\
        + gchunk.cat+', [correct]: '\
        + ('φ' if gchunk.gold_sent=='' else gchunk.gold_sent)\
        + ', [weight]: '\
        + str(round(gchunk.weight,2))\
        +" '")
    #If a chunk corresponding a token or tokens
    if not gchunk.is_insert_chunk():
        if not gchunk.is_modified:
            if count_false_positive(gchunk) > 0:
                s += '<span class="bluew'+str(round(gchunk.weight*100))+'" '+mouseover+'>'+\
                     gchunk.orig_sent  + '</span> '
            else:
                s += gchunk.orig_sent
        else:
            s += '<span class="redw'+str(round(gchunk.weight*100))+'" '+mouseover+'>'+\
                 gchunk.orig_sent +'</span> '
    # If a chunk corresponding an insert
    else:
        if gchunk.is_modified:
            s += '<span class="redw'+str(round(gchunk.weight*100))+'" '+mouseover+'>'+' '+'</span> '
        else:
            if count_false_positive(gchunk) > 0:
                s += '<span class="bluew'+str(round(gchunk.weight*100))+'" '+mouseover+'>'+' '+'</span> '
            else:
                s+=' '
    return s


def count_false_positive(chunk) -> int:
    ret = 0
    for evalinfo in chunk.sys2eval:
        if evalinfo.is_modified and not evalinfo.is_correct:
            ret += 1
    return ret


def generate_css(number_of_systems: int) -> str:
    css_str = '<style type="text/css">\n'
    delta = 1 / number_of_systems
    color = dict()
    color['red'] = '255,0,0,'
    color['blue'] = '0,0,255,'
    for i in range(number_of_systems + 1):
        if delta*i <0.7: s = '.redw'+str(round(delta*i*100))+'{ background-color: rgb('+color['red']+str(min(1.0, max(delta*i, 0.1)))+')}'
        else: s = '.redw'+str(round(delta*i*100))+'{ background-color: rgb('+color['red']+str(min(1.0, max(delta*i, 0.1)))+');font-weight:900;}'
        css_str += s + '\n'
    for i in range(number_of_systems + 1):
        if delta*i <0.7: s = '.bluew'+str(round(delta*i*100))+'{ background-color: rgb('+color['blue']+str(min(1.0, max(delta*i, 0.1)))+')}'
        else: s = '.bluew'+str(round(delta*i*100))+'{ background-color: rgb('+color['blue']+str(min(1.0, max(delta*i, 0.1)))+');font-weight:900;}'
        css_str += s + '\n'
    css_str += '</style>\n'
    return css_str