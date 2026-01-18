import streamlit as st
from pdf_reader import extract_text_from_pdf
from claim_extractor import extract_claims
from verifier import verify_claim

st.set_page_config(page_title="CheckM8 - Fact Checker", layout="wide")

st.title("♟️ CheckM8 — AI Fact Checking Assistant")
st.write("Upload a PDF and verify factual claims using live web data.")

file = st.file_uploader("Upload PDF", type=["pdf"])

if file:
    with st.spinner("Reading PDF..."):
        text = extract_text_from_pdf(file)

    st.success("PDF processed")

    with st.expander("📄 View Extracted Text"):
        st.text_area("Text", text, height=300)

    with st.spinner("Extracting factual claims..."):
        claims = extract_claims(text)

    if not claims:
        st.warning("No factual claims found.")
    else:
        # ---------- VERIFY ALL CLAIMS ----------
        results = []

        with st.spinner("🔍 Verifying all claims with live web data..."):
            for c in claims:
                res = verify_claim(c["claim"])
                results.append({
                    "claim": c["claim"],
                    "category": c["category"],
                    "result": res
                })

        # ---------- FEATURE 1: SUMMARY DASHBOARD ----------
        total = len(results)
        verified = sum(1 for r in results if r["result"]["verdict"] == "VERIFIED")
        inaccurate = sum(1 for r in results if r["result"]["verdict"] == "INACCURATE")
        false = sum(1 for r in results if r["result"]["verdict"] == "FALSE")

        st.subheader("📊 Fact Check Summary")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Claims", total)
        c2.metric("✅ Verified", verified)
        c3.metric("⚠️ Inaccurate", inaccurate)
        c4.metric("❌ False", false)

        st.markdown("---")
        st.subheader("🧠 Detailed Claim Analysis")

        # ---------- DISPLAY RESULTS ----------
        for i, r in enumerate(results, 1):
            st.markdown(f"### {i}. {r['claim']}")

            res = r["result"]

            if res["verdict"] == "VERIFIED":
                st.success("✅ VERIFIED")
            elif res["verdict"] == "INACCURATE":
                st.warning("⚠️ INACCURATE / OUTDATED")
            else:
                st.error("❌ FALSE")

            st.write("**Explanation:**", res["explanation"])

            # ---------- FEATURE 4: AUTO CORRECTION ----------
            if res["verdict"] != "VERIFIED" and res.get("correct_info"):
                st.success("✍️ Suggested Correction:")
                st.write(res["correct_info"])

            if res.get("sources"):
                st.write("**Sources:**")
                for s in res["sources"]:
                    st.write(s)

            st.markdown("---")
