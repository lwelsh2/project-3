"""
Flask web site with vocabulary matching game
(identify vocabulary words that can be made
from a scrambled string)
"""

import flask
import logging

# Our modules
from src.letterbag import LetterBag
from src.vocab import Vocab
from src.jumble import jumbled
import src.config as config

###
# Globals
###
app = flask.Flask(__name__)

CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY  # Should allow using session variables

# One shared 'Vocab' object, read-only after initialization,
# shared by all threads and instances.
WORDS = Vocab(CONFIG.VOCAB)
SEED = CONFIG.SEED

try:
    SEED = int(SEED)
except ValueError:
    SEED = None

###
# Pages
###

@app.route("/")
@app.route("/index")
def index():
    flask.g.vocab = WORDS.as_list()
    flask.session["target_count"] = min(len(flask.g.vocab), CONFIG.SUCCESS_AT_COUNT)
    flask.session["jumble"] = jumbled(
        flask.g.vocab, flask.session["target_count"], seed=None if not SEED or SEED < 0 else SEED)
    flask.session["matches"] = []
    app.logger.debug("Session variables have been set")
    assert flask.session["matches"] == []
    assert flask.session["target_count"] > 0
    app.logger.debug("At least one seems to be set correctly")
    return flask.render_template('vocab.html')

@app.route("/keep_going")
def keep_going():
    flask.g.vocab = WORDS.as_list()
    return flask.render_template('vocab.html')

@app.route("/success")
def success():
    return flask.render_template('success.html')

@app.route("/_check", methods=["POST"])
def check():
    app.logger.debug("Entering check")
    text = flask.request.form["attempt"]
    jumble = flask.session["jumble"]
    matches = flask.session.get("matches", [])
    in_jumble = LetterBag(jumble).contains(text)
    matched = WORDS.has(text)

    if matched and in_jumble and not (text in matches):
        matches.append(text)
        flask.session["matches"] = matches
        result = {
            "success": True,
            "message": f"You found {text}",
            "matches": matches
        }
    elif text in matches:
        result = {
            "success": False,
            "message": f"You already found {text}",
            "matches": matches
        }
    elif not matched:
        result = {
            "success": False,
            "message": f"{text} isn't in the list of words",
            "matches": matches
        }
    elif not in_jumble:
        result = {
            "success": False,
            "message": f'"{text}" can\'t be made from the letters {jumble}',
            "matches": matches
        }
    else:
        app.logger.debug("This case shouldn't happen!")
        assert False

    if len(matches) >= flask.session["target_count"]:
        return flask.jsonify({"success": True, "redirect": True})  # Redirect to success page
    else:
        return flask.jsonify(result)

@app.errorhandler(404)
def error_404(e):
    app.logger.warning("++ 404 error: {}".format(e))
    return flask.render_template('404.html'), 404

@app.errorhandler(500)
def error_500(e):
    app.logger.warning("++ 500 error: {}".format(e))
    assert not True
    return flask.render_template('500.html'), 500

@app.errorhandler(403)
def error_403(e):
    app.logger.warning("++ 403 error: {}".format(e))
    return flask.render_template('403.html'), 403

if __name__ == "__main__":
    if CONFIG.DEBUG:
        app.debug = True
        app.logger.setLevel(logging.DEBUG)
        app.logger.info("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0", debug=CONFIG.DEBUG)





