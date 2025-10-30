from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

CSV_PATH = "SEMA_booths_cleaned.csv"


def load_data():
    df = pd.read_csv(CSV_PATH, dtype=str, engine="python")
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.fillna("")

    # Ensure required columns exist
    for col in ["hall", "booth_number", "company_name", "technology", "notes", "preshow_notes", "postshow_notes"]:
        if col not in df.columns:
            df[col] = ""

    # Clean and normalize text
    df = df.applymap(lambda x: str(x).replace("|", "").strip() if isinstance(x, str) else "")

    return df


def save_data(df):
    df.to_csv(CSV_PATH, index=False)


@app.route("/")
def index():
    df = load_data()
    halls = sorted(df["hall"].dropna().unique())
    return render_template("index.html", halls=halls)


@app.route("/booths")
def booths():
    hall = request.args.get("hall", "").strip()
    df = load_data()
    hall_df = df[df["hall"].str.lower() == hall.lower()]

    grouped = []
    for booth, group in hall_df.groupby("booth_number"):
        contacts = []
        for _, r in group.iterrows():
            name = f"{r['first_name']} {r['last_name']}".strip()
            contacts.append(f"{name} — {r['job_title']} ({r['email_address']})")
        record = group.iloc[0].to_dict()
        record["contacts"] = "<br>".join(contacts)
        grouped.append(record)

    return jsonify(grouped)


@app.route("/booth/<booth_number>")
def booth_details(booth_number):
    df = load_data()
    booth_number = str(booth_number).strip().lower()
    rows = df[df["booth_number"].str.lower() == booth_number]

    if rows.empty:
        return jsonify({"error": "Booth not found"}), 404

    contacts = []
    for _, r in rows.iterrows():
        name = f"{r['first_name']} {r['last_name']}".strip()
        contacts.append(f"{name} — {r['job_title']} ({r['email_address']})")

    row = rows.iloc[0].to_dict()

    # Clean display text
    for key in ["notes", "preshow_notes", "postshow_notes"]:
        val = row.get(key, "")
        if not isinstance(val, str) or val.lower() in ["nan", "none", "|"]:
            row[key] = ""
        else:
            row[key] = val.strip().replace("|", "")

    row["contacts"] = "<br>".join(contacts)
    return jsonify(row)


@app.route("/booth/<booth_number>", methods=["POST"])
def save_notes(booth_number):
    try:
        data = request.get_json()
        note = data.get("note", "").strip()
        preshow = data.get("preshow", "").strip()
        postshow = data.get("postshow", "").strip()

        df = load_data()
        booth_number = str(booth_number).strip().lower()
        mask = df["booth_number"].str.lower() == booth_number

        if not mask.any():
            return jsonify({"error": f"Booth {booth_number} not found"}), 404

        df.loc[mask, "notes"] = note
        df.loc[mask, "preshow_notes"] = preshow
        df.loc[mask, "postshow_notes"] = postshow

        save_data(df)

        return jsonify({"message": f"✅ Notes saved for Booth {booth_number}"}), 200
    except Exception as e:
        return jsonify({"error": f"⚠️ Error saving note: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
