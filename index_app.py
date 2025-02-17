from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("test_page.html")

# @app.route('/process', methods=['POST'])
# def process():
#     youtube_url = request.form.get("youtube_url")
#     # Process the YouTube URL (placeholder logic)
#     return f"You submitted: {youtube_url}"

if __name__ == '__main__':
    app.run(debug=True)
