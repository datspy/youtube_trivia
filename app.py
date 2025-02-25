from flask import Flask, redirect, render_template, request, flash, url_for
import googleapiclient.errors
from analysis import run_analysis


app = Flask(__name__)
app.secret_key = "flash_message_key"
display_flag=False

@app.route("/")
def index():	
	return render_template("index.html")

@app.route("/submit", methods=['POST', 'GET'])
def url_submit():
	if request.method == "POST":
			try:		
				video_id = str(request.form["video_url"]).split('=')[1].split('&')[0]
				return redirect(url_for("analysis", vid=video_id))
			except:
				flash(fr"This URL is invalid!!", category="error")
				return render_template("index.html")
	else:
		return render_template("index.html")		
	
@app.route("/<vid>")
def analysis(vid):

	try:
		flag, trivia_list, ch_stats, videos_by_time_list =run_analysis(vid)	
		return render_template("display.html", videos=trivia_list, ch=ch_stats, table_data=videos_by_time_list)
	except googleapiclient.errors.HttpError as e:
		if "quota" in str(e.reason):
			error_msg = f"The API Quota has been exceeded for today!!\n" \
				f"Please try again tomorrow!"
			display_text = error_msg.split('\n')
			flash(display_text, category="api_error")
			return render_template("index.html")
		else:
			flash(f"{e}", category="error")
			return render_template("index.html")
	except Exception as e:
		flash(f"{e}", category="error")
		return render_template("index.html")

	

if __name__ == "__main__":
    app.run(debug=True)
