# from flask import Flask, render_template, request, jsonify
# import pandas as pd
# import os

# app = Flask(__name__)
# CSV_PATH = "SEMA_booths_cleaned.csv"


# # === Load & clean CSV ===
# def load_data():
#     if not os.path.exists(CSV_PATH):
#         raise FileNotFoundError(f"CSV not found at {CSV_PATH}")

#     df = pd.read_csv(CSV_PATH, dtype=str, engine="python")
#     df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
#     df = df.fillna("")

#     # Ensure required columns exist
#     for col in ["hall", "booth_number", "company_name", "technology"]:
#         df[col] = df[col].astype(str).str.strip()
#     for col in ["notes", "preshow_notes", "postshow_notes"]:
#         if col not in df.columns:
#             df[col] = ""

#     return df


# # === Group contacts per booth ===
# def group_booths(df):
#     grouped = (
#         df.groupby(
#             ["hall", "booth_number", "company_name", "technology", "website", "revenue"],
#             dropna=False
#         )
#         .agg({
#             "first_name": lambda x: "; ".join(x.dropna().unique()),
#             "last_name": lambda x: "; ".join(x.dropna().unique()),
#             "job_title": lambda x: "; ".join(x.dropna().unique()),
#             "direct_phone_number": lambda x: "; ".join(x.dropna().unique()),
#             "mobile_phone": lambda x: "; ".join(x.dropna().unique()),
#             "email_address": lambda x: "; ".join(x.dropna().unique()),
#             "notes": " | ".join,
#             "preshow_notes": " | ".join,
#             "postshow_notes": " | ".join
#         })
#         .reset_index()
#     )
#     return grouped


# @app.route("/")
# def index():
#     df = load_data()
#     grouped = group_booths(df)
#     halls = sorted(grouped["hall"].dropna().unique())
#     return render_template("index.html", halls=halls)


# @app.route("/booths")
# def booths():
#     hall = request.args.get("hall", "").strip().lower()
#     df = load_data()
#     grouped = group_booths(df)
#     hall_df = grouped[grouped["hall"].str.lower() == hall]
#     return jsonify(hall_df.to_dict(orient="records"))


# @app.route("/booth/<booth_number>")
# def booth_details(booth_number):
#     df = load_data()
#     grouped = group_booths(df)
#     booth_number = str(booth_number).strip().lower()
#     row = grouped[grouped["booth_number"].str.lower() == booth_number]

#     if row.empty:
#         return jsonify({"error": "Booth not found"}), 404

#     return jsonify(row.iloc[0].to_dict())


# @app.route("/booth/<booth_number>", methods=["POST"])
# def save_notes(booth_number):
#     try:
#         data = request.get_json()
#         note = data.get("note", "").strip()
#         preshow = data.get("preshow", "").strip()
#         postshow = data.get("postshow", "").strip()

#         df = load_data()
#         mask = df["booth_number"].str.lower() == str(booth_number).lower()

#         if not mask.any():
#             return jsonify({"error": "❌ Booth not found"}), 404

#         df.loc[mask, "notes"] = note
#         df.loc[mask, "preshow_notes"] = preshow
#         df.loc[mask, "postshow_notes"] = postshow
#         df.to_csv(CSV_PATH, index=False)

#         return jsonify({"message": f"✅ Notes saved for Booth {booth_number}"})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# if __name__ == "__main__":
#     app.run(debug=True)





from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

CSV_PATH = "SEMA_booths_cleaned.csv"


# -----------------------------
# Load and clean CSV data
# -----------------------------
def load_data():
    df = pd.read_csv(CSV_PATH, dtype=str, engine="python")
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.fillna("")

    # Ensure expected columns
    required = [
        "hall", "booth_number", "company_name", "technology",
        "website", "revenue",
        "first_name", "last_name", "job_title",
        "direct_phone_number", "mobile_phone", "email_address",
        "notes", "preshow_notes", "postshow_notes"
    ]
    for col in required:
        if col not in df.columns:
            df[col] = ""

    # Basic cleanup
    df = df.applymap(lambda x: str(x).strip() if isinstance(x, str) else "")
    return df


# -----------------------------
# Save cleaned CSV data
# -----------------------------
def save_data(df):
    for col in ["notes", "preshow_notes", "postshow_notes"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r"\|+", "", regex=True).str.strip()
    df.to_csv(CSV_PATH, index=False)


# -----------------------------
# Homepage: hall dropdown
# -----------------------------
@app.route("/")
def index():
    df = load_data()
    halls = sorted(df["hall"].dropna().unique())
    return render_template("index.html", halls=halls)


# -----------------------------
# Get all booths for a hall
# -----------------------------
@app.route("/booths")
def booths():
    hall = request.args.get("hall", "").strip()
    df = load_data()
    hall_df = df[df["hall"].str.lower() == hall.lower()]

    booths_data = []
    for booth, group in hall_df.groupby("booth_number"):
        booth_info = group.iloc[0].to_dict()
        booth_info["contacts"] = len(group)
        booths_data.append(booth_info)

    return jsonify(booths_data)


# -----------------------------
# Get single booth details (all contacts)
# -----------------------------
@app.route("/booth/<booth_number>")
def booth_details(booth_number):
    df = load_data()
    booth_number = str(booth_number).strip().lower()
    rows = df[df["booth_number"].str.lower() == booth_number]

    if rows.empty:
        return jsonify({"error": "Booth not found"}), 404

    # Pick main booth details (first row)
    booth = rows.iloc[0].to_dict()

    # Clean notes for display
    for field in ["notes", "preshow_notes", "postshow_notes"]:
        val = str(booth.get(field, "")).strip()
        if val in ["nan", "none", "|", "||", "|||", "||||", "|||||"]:
            booth[field] = ""
        else:
            booth[field] = val.replace("|", "").strip()

    # Combine all contacts (multiple rows)
    first_names = rows["first_name"].tolist()
    last_names = rows["last_name"].tolist()
    job_titles = rows["job_title"].tolist()
    phones = rows["direct_phone_number"].tolist()
    mobiles = rows["mobile_phone"].tolist()
    emails = rows["email_address"].tolist()

    # Format contacts for front-end
    booth["first_name"] = "; ".join(first_names)
    booth["last_name"] = "; ".join(last_names)
    booth["job_title"] = "; ".join(job_titles)
    booth["direct_phone_number"] = "; ".join(phones)
    booth["mobile_phone"] = "; ".join(mobiles)
    booth["email_address"] = "; ".join(emails)

    return jsonify(booth)


# -----------------------------
# Save Notes (AJAX)
# -----------------------------
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


# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
