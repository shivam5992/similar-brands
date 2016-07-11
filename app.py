from flask import *
from eda import Model

app = Flask(__name__)
app.secret_key = 'shivam_bansal'

@app.route("/", methods = ['GET', 'POST'])
def index():
	message = False
	brands = False
	if request.method == 'POST':
		val = request.form['inp_brand']
		limit = request.form['limit']
		brands = Model().get_most_similar(val, int(limit))
		if not brands:
			message = "No Similar Brand Found"
	return render_template("index.html", brands = brands, message = message)

app.run(debug = True)