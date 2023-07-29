from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import requests
from bs4 import BeautifulSoup
import time
from flask import Flask, render_template, request
import os


def compute_similarity(text1, text2):
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    cosine = cosine_similarity(vectors)
    return cosine[0, 1]  # this will give you the cosine similarity score


def get_similiarity_score(original_content, test_content):
    similiary_score = compute_similarity(original_content, test_content)

    if similiary_score > 0.8:
        similiarity_feedback = "This article is heavily relying on same words and should be entirely regenerated"
    elif similiary_score > 0.3:
        similiarity_feedback = "This article is significantly relying on same words, reconsider manually rewriting some paragraphs"
    elif similiary_score > 0.1:
        similiarity_feedback = "This article has some similarity, review carefully"
    else:
        similiarity_feedback = "This content does not carry similarity risk."
    return similiary_score, similiarity_feedback

# TO FIND MATCHING SEQUENCES FOR THE FEATURE WHERE OUTPUT IS DISPLAYED IN RED


def find_matching_sequences(original, generated, sequence_length=5):
    original_words = original.split()
    generated_words = generated.split()

    matching_sequences = []

    for i in range(len(original_words) - sequence_length + 1):
        sequence = original_words[i:i+sequence_length]
        sequence_str = ' '.join(sequence)
        if sequence_str in generated:
            matching_sequences.append(sequence_str)

    return matching_sequences

# TO SHOW PLAGIARISED CONTENT IN RED COLOR


def highlight_matching_sequences(original, generated, sequence_length=5):
    sequences = find_matching_sequences(original, generated, sequence_length)
    for seq in sequences:
        highlighted = f'<span style="color:red">{seq}</span>'
        generated = generated.replace(seq, highlighted)
    return generated

# For scraper


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
}

# Source article from user, either by URL or pasted content


def get_article():
    print("Please enter your article (finish with 'BZNEURO'):")
    lines = []
    while True:
        line = input()
        if line == "BZNEURO":
            break
        lines.append(line)
    return '\n'.join(lines)

# Scrape content of the URL if user provides article via URL


def scrape_url_content(url):
    try:
        time.sleep(5)  # delay of 5 seconds
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        content = []

        # Check for headline (typically in h1, h2, or title tags)
        headline = soup.find(['h1', 'h2', 'title'])
        if headline:
            content.append(headline.text)

        # Add all paragraph tags to the content list
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            content.append(p.text)

        return '\n\n'.join(content)

    except requests.RequestException as e:
        return f"Error occurred: {e}"


# ... [your other functions]


def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    # remove all javascript and stylesheet code
    for script in soup(["script", "style"]):
        script.extract()
    return " ".join(soup.stripped_strings)


# FLASK APP
app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    feedback = ""
    score = ""
    highlighted_content = ""

    if request.method == "POST":
        original_content = request.form.get("original_content")
        test_content = request.form.get("test_content")

        # Check if the original_content is a URL
        if original_content.startswith("http"):
            original_content = scrape_url_content(original_content)

        test_content = extract_text_from_html(test_content)

        # Compute the similiarity score for the test content
        similarity_score, feedback = get_similiarity_score(
            original_content, test_content)

        score = f"{similarity_score * 100:.2f}%"
        highlighted_content = highlight_matching_sequences(
            original_content, test_content)

    return render_template("index.html", feedback=feedback, score=score, highlighted_content=highlighted_content)


if __name__ == "__main__":
    app.run(debug=True)
