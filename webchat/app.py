import logging
import os
import sys

dir_path = os.path.dirname(os.path.realpath(__file__)) + "/"

from flask import Flask, render_template, request, send_from_directory
from flask import jsonify

sys.path.append('..')
import chatbot.AIMLEngine as AIMLBasedLookup
import chatbot.QAEngine as SimilarityBasedLookup
import chatbot.WikiApi as WikiApi

logging.basicConfig(level=logging.CRITICAL)  # change critical to info to display information
app = Flask(__name__)
# do the top level import if possible, required for heroku hosting
try:
    AIMLBasedLookup.load_aiml(dir_path + '../dataset/aiml_set.xml')
    # Similarity based lookup will use data from our csv file, load it in
    SimilarityBasedLookup.load_qa_csv(dir_path + '../dataset/thyroid-problems-qa.csv')
except:
    pass


def get_answer(user_query):
    aiml_answer = AIMLBasedLookup.get_response(user_query)  # first use aiml for lookup
    if aiml_answer.split("#")[0] == "inaiml":
        return (aiml_answer.split("#")[1])
    if aiml_answer.split("#")[0] == "wikishort":
        ok, wikipedia_answer = WikiApi.get_from_wiki(aiml_answer.split("#")[1])
        if not ok:
            # if not able to find answer on wikipedia give our QA another go
            ok, similarity_answer = SimilarityBasedLookup.get_answer(user_query, confidence_threshold=0.25)
            if ok:
                return (similarity_answer)
            else:
                # return("Sorry, please be more precise with your question")
                return ("Weren't able to find your term on Wikipedia nor our QA dataset, please try to rephrase")
        else:
            return (wikipedia_answer)
    if aiml_answer.split("#")[0] == "wikilong":
        ok, wikipedia_answer = WikiApi.get_from_wiki(aiml_answer.split("#")[1], sentences=10)
        if not ok:
            # if not able to find answer on wikipedia give our QA another go
            ok, similarity_answer = SimilarityBasedLookup.get_answer(user_query, confidence_threshold=0.25)
            if ok:
                return (similarity_answer)
            else:
                # return("Sorry, please be more precise with your question")
                return ("Weren't able to find your term on Wikipedia nor our QA dataset, please try to rephrase")
        else:
            return (wikipedia_answer)
    if aiml_answer.split("#")[0] == "notinaiml":  # if answer is not in aiml use Similarity based lookup
        ok, similarity_answer = SimilarityBasedLookup.get_answer(user_query, confidence_threshold=0.25)
        if ok:
            return (similarity_answer)
        else:
            return ("Sorry, please be more precise with your question")


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/docs/<path:filename>', methods=['GET', 'POST'])
def index(filename):
    filename = filename or 'index.html'
    if request.method == 'GET':
        return send_from_directory(dir_path + "../docs/html/chatbot", filename)

    return jsonify(request.data)


@app.route("/process", methods=["POST"])
def response():
    msg = request.form["msg"]
    # return(msg)
    msg = get_answer(msg)
    return msg


if __name__ == "__main__":
    # AIML Based lookup will use data from our xml file, load it in
    AIMLBasedLookup.load_aiml(dir_path + '../dataset/aiml_set.xml')
    # Similarity based lookup will use data from our csv file, load it in
    SimilarityBasedLookup.load_qa_csv(dir_path + '../dataset/thyroid-problems-qa.csv')
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port, host='0.0.0.0', debug=True)
