from flask import Flask, redirect, render_template, request, flash, url_for
from analysis import run_analysis


app = Flask(__name__)
app.secret_key = "manbearpig_MUDMAN888"
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
				flash(fr"This URL is invalid!!")
				return render_template("index.html")
	else:
		return render_template("index.html")		
	
@app.route("/<vid>")
def analysis(vid):

	# trivia_list, ch_stats, videos_by_time_list =run_analysis(vid)
	trivia_list = [{'type': 'Most Engaged Video',
				 'title': 'Learning Hindi Ep.6 🕺',
				 'PublishedDate': '2022-08-13',
				 'id': 'Ia8s0SCrp6Q',
				 'text': '486,794 views | 86,504 likes | 2,337 comments',
				 'scores': 'Engagement Score: 18.25'},
				 {'type': 'Most Viewed Video',
	  			'title': '𝕍𝕚𝕓𝕖 𝕋𝕚𝕞𝕖',
				'PublishedDate': '2022-01-17',
				'id': 'Efgkc7sHJsY',
				'text': '2,721,566 views | 192,505 likes | 7,146 comments',
				'scores': 'Engagement Score: 7.34'},
				{'type': 'Most Liked Video',
	 			'title': '𝕍𝕚𝕓𝕖 𝕋𝕚𝕞𝕖',
				'PublishedDate': '2022-01-17',
				'id': 'Efgkc7sHJsY',
				'text': '2,721,566 views | 192,505 likes | 7,146 comments',
				'scores': 'Engagement Score: 7.34'},
				{'type': 'Most Commented Video',
	 			'title': 'Dreams that came TRUE! 🧛‍♂️',
				'PublishedDate': '2021-10-26',
	 			'id': 'Sk_gIRhJ6-M',
				'text': '385,299 views | 45,630 likes | 16,923 comments',
				'scores': 'Engagement Score: 16.23'}]


	text_title_one = "2021-06-23"
	text_title_two = "2025-02-13"

	text_subtitle = fr"JK Published 7 videos in the last 60 days!!"
	# table_data = [["00-06", "0"],
    #               ["06-12", "112"],
    #               ["12-18", "234"],
    #               ["18-24", "765"]]
	table_data = [["00:00 - 05:59", "0"],
                  ["06:00 - 11:59", "112"],
                  ["12:00 - 17:59", "234"],
                  ["18:00 - 23:59", "765"]]
	
	
	# return render_template("display.html", videos=trivia_list, f_date=ch_stats['first_video'], l_date=ch_stats['last_video'], text_subtitle=text_subtitle, table_data=videos_by_time_list)
	return render_template("display.html", videos=trivia_list, f_date=text_title_one, l_date=text_title_two, text_subtitle=text_subtitle, table_data=table_data)


if __name__ == "__main__":
    app.run(debug=True)
