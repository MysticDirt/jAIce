# Run by typing python3 main.py

# **IMPORTANT:** only collaborators on the project where you run
# this can access this web server!

# import basics
import os

# import stuff for our web server
from flask import Flask, request, redirect, url_for, render_template, session
from utils import get_base_url
# import stuff for our models
#from aitextgen import aitextgen (deprecated)
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch

# load up a model from memory. Note you may not need all of these options.
# ai = aitextgen(model_folder="model/",
#                tokenizer_file="model/aitextgen.tokenizer.json", to_gpu=False)

#ai = aitextgen(model_folder="model/no_q_10kgpt2_model/", to_gpu=False)

#Set up HuggingFace Transformers model and tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("app/model/no_q_10kgpt2_model/")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# setup the webserver
# port may need to be changed if there are multiple flask servers running on same server
port = 15459
#base_url = get_base_url(port)    #for running on codingcamp
base_url = '/'  #for running locally


# if the base url is not empty, then the server is running in development, and we need to specify the static folder so that the static files are served
if base_url == '/':
    app = Flask(__name__)
else:
    app = Flask(__name__, static_url_path=base_url+'static')

app.secret_key = os.urandom(64)

# set up the routes and logic for the webserver


@app.route(f'{base_url}')
def home():
    if 'data' in session:
        data = session['data']
        prev_prompt = session['prev_prompt']
        prev_temp = session['prev_temp']
        prev_top_p = session['prev_top_p']
        return render_template('writer_home.html', generated=data, prompt=prev_prompt, temperature=prev_temp, top_p=prev_top_p)
    else:
        return render_template('writer_home.html', generated=None, prompt="", temperature=75, top_p=95)


@app.route(f'{base_url}', methods=['POST'])
def home_post():
    return redirect(url_for('home'))


"""@app.route(f'{base_url}')
def results():
    if 'data' in session:
        data = session['data']
        return render_template('writer_home.html', generated=data)
    else:
        return render_template('writer_home.html', generated=None)"""


@app.route(f'{base_url}/generate_text/', methods=["POST"])
def generate_text():
    """
    view function that will return json response for generated text.
    """

    prompt = request.form['prompt']
    temp = request.form['temperature']
    top_p = request.form['top_p']
    print(prompt)
    print(temp)
    print(top_p)
    if prompt is not None:
        input_ids = tokenizer.encode(prompt + " {", return_tensors='pt').to(device)
        generated_ids = model.generate(
            input_ids,
            max_length=300,
            temperature=float(temp)/100,
            top_p=float(top_p)/100,
            do_sample=True, #Enable sampling to avoid greedy generation
            pad_token_id=tokenizer.eos_token_id #EOS token to prevent errors in generation
        )
        """generated = ai.generate(
            n=1,
            #batch_size=3, (Doesn't work past transformers version 4.21.3)
            prompt=str(prompt) + " {",
            max_length=300,
            temperature=float(temp)/100,
            top_p=float(top_p)/100,
            return_as_list=True
        )"""
        generated = tokenizer.decode(generated_ids[0], skip_special_tokens=True) #decode the output
        print(generated)
        generated_string = generated.split("{")[-1].strip() if "{" in generated else generated #Post process output
    else:
        generated_string = "Input a prompt."

    data = {'generated_ls': [generated_string]}
    session['data'] = generated_string
    session['prev_prompt'] = str(prompt)
    session['prev_temp'] = int(temp)
    session['prev_top_p'] = int(top_p)
    return redirect(url_for('home', _anchor='trythemodel'))

# define additional routes here
# for example:
@app.route(f'{base_url}/team_members')
def team_members():
    return render_template('team_members.html')


if __name__ == '__main__':
    # IMPORTANT: change url to the site where you are editing this file.
    website_url = '127.0.0.1'

    print(f'Try to open\n\n    http://{website_url}:{port}' + base_url + '\n\n')
    app.run(host='0.0.0.0', port=port, debug=True)


#@app.route('/')
#def writer_home():
#    return render_template('writer_home.html')