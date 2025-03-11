from flask import Flask, redirect, render_template, request, flash, url_for
import logging
from logging.config import dictConfig
import googleapiclient.errors
from analysis import run_analysis


app = Flask(__name__)
app.secret_key = "flash_message_key"
display_flag=False

logger = logging.getLogger("root")
logger.setLevel(logging.WARNING)


dictConfig(
	{
        "version": 1,
		"formatters": {
            "default": {
                "format": "[%(levelname)s] [%(asctime)s] %(processName)s %(message)s",
            }
        },    
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "logs/app.log",
                "maxBytes": 100000000,
                "backupCount": 3,
                "formatter": "default",
            },
        },
        "root": {"level": "INFO", "handlers": ["file"]},
    }
)


@app.route("/")
def index():	

	return render_template("index.html")


@app.route("/submit", methods=['POST', 'GET'])
def url_submit():	
	
	if request.method == "POST":
			try:
				vurl = str(request.form["video_url"])
				logger.warning(f"URL: {vurl}")
				video_id = vurl.split('=')[1].split('&')[0]
				logger.warning(f"VideoID: {video_id}")
				return redirect(url_for("stats", vid=video_id))			
			except:
				flash(fr"This URL is invalid!!", category="error")
				logger.error("This URL is invalid!!")
				return render_template("index.html")				
	else:
		return render_template("index.html")


@app.route("/stats/<vid>", methods=['POST', 'GET'])
def stats(vid):

		try:								
			low_engagement, trivia_list, ch_stats, videos_by_time_list =run_analysis(vid)
			if low_engagement:
				logger.error("Channel Does Not Have Enough Engagement For Analysis!")
				flash("Channel Does Not Have Enough Engagement For Analysis!", category="error")
				return redirect(url_for("index"))
			else:
				return render_template("display.html", videos=trivia_list, ch=ch_stats, table_data=videos_by_time_list)
		except googleapiclient.errors.HttpError as e:
			if "quota" in str(e.reason):
				error_msg = f"The API Quota has been exceeded for today!!\n" \
					f"Please try again tomorrow!"
				logger.error(f"{error_msg}")
				display_text = error_msg.split('\n')
				flash(display_text, category="api_error")
				return render_template("index.html")
			else:			
				flash(f"{e}", category="error")
				return render_template("index.html")
		except Exception as e:
			logger.error(f"{e}")
			flash(f"{e}", category="error")			
			return redirect(url_for("index"))	
			

if __name__ == "__main__":
	
	app.run(debug=True)
