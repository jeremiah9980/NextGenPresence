from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string(open('tagger.html').read())

@app.route('/tag', methods=['POST'])
def tag():
    mac = request.form.get('mac')
    name = request.form.get('name')
    # Save logic here
    return f"Tagged {mac} as {name}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050)
