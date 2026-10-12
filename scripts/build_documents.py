from pathlib import Path
from shutil import copy2

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, Mm


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(r"C:\Users\D.T.D.Wijesinghe\Documents\Codex\2026-10-12\che\outputs")
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = Path(r"C:\Users\D.T.D.Wijesinghe\Documents\3YS1\ML Project")


def set_a4(section):
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(15)
    section.bottom_margin = Mm(15)
    section.left_margin = Mm(18)
    section.right_margin = Mm(18)


def style_doc(doc):
    styles = doc.styles
    styles["Normal"].font.name = "Aptos"
    styles["Normal"].font.size = Pt(9.5)
    styles["Title"].font.name = "Aptos Display"
    styles["Title"].font.size = Pt(18)
    styles["Heading 1"].font.name = "Aptos Display"
    styles["Heading 1"].font.size = Pt(13)
    styles["Heading 2"].font.name = "Aptos Display"
    styles["Heading 2"].font.size = Pt(11)


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for cell, text in zip(table.rows[0].cells, headers):
        cell.text = str(text)
    for row in rows:
        cells = table.add_row().cells
        for cell, text in zip(cells, row):
            cell.text = str(text)
    return table


def build_main_report():
    source = SOURCE / "01_IT3091_Final_Group_Report_and_Evidence.docx"
    target = OUT / "01_IT3091_Final_Group_Report_and_Evidence_REVISED.docx"
    copy2(source, target)
    doc = Document(target)
    doc.add_page_break()
    doc.add_heading("Final Revision Addendum", level=1)
    doc.add_paragraph(
        "This addendum records the executed revision of the prediction systems. The original cover page is preserved unchanged. "
        "The revised price scope is Colombo next-week wholesale price prediction, while the yield scope is district-level crop yield prediction. "
        "The revised pipelines use separate observational units because forcing seasonal yield and weekly price targets into one table reduced valid evidence."
    )
    doc.add_heading("Revised observational units", level=2)
    doc.add_paragraph(
        "Price rows represent one genuine Colombo/Pettah crop-date observation with a target equal to the mean wholesale price in the following calendar week. "
        "Yield rows represent one genuine district-crop-season-year production observation matched to a district weather location and a three-month pre-forecast weather window."
    )
    add_table(doc, ["Task", "Original records", "Valid source", "After cleaning", "Final labelled", "Train", "Validation", "Test"], [
        ["Colombo next-week price", "47,886", "42,056", "42,056", "39,377", "9,270", "7,320", "22,787"],
        ["District crop yield", "94,755", "16,626", "15,698", "15,698", "9,620", "2,982", "3,096"],
    ])
    doc.add_heading("Executed evaluation", level=2)
    add_table(doc, ["Task", "Selected model", "Test MAE", "Test RMSE", "Test R2", "Baseline test R2"], [
        ["Colombo next-week price", "Gradient Boosting", "64.76 Rs/kg", "137.44 Rs/kg", "0.363", "-0.115"],
        ["District crop yield", "Random Forest", "2.44 t/ha", "8.28 t/ha", "0.124", "-0.018"],
    ])
    doc.add_paragraph(
        "The revised price result is an improvement over the previous negative-R2 monthly price result, but it remains a market signal rather than a guaranteed forecast. "
        "The daily Colombo source ends in 2025, so the application shows a data-freshness warning instead of presenting a historical backtest as a live October 2026 forecast."
    )
    doc.add_heading("Evidence and approval status", level=2)
    doc.add_paragraph(
        "The revised code, processed datasets, trained pipelines, metrics, and record-count evidence are included in the revised project package. "
        "The existing stakeholder review document is preserved. Because the original review concerns the earlier next-month/national framing, renewed stakeholder approval is required before claiming that the revised Colombo next-week scope was approved."
    )
    doc.add_heading("Reproducibility", level=2)
    doc.add_paragraph("Run scripts/revised_pipeline.py with the supplied Colombo daily workbook to regenerate the two CSV datasets, trained pipelines, metadata, metrics, and record-count table. Run streamlit run app.py to open both prediction modules.")
    doc.save(target)
    return target


PERSONAL = {
    "03_Personal_Learning_Journey_IT24100858_REVISED.docx": (
        "IT24100858 - Wijesinghe.D.T.D",
        "My responsibility was production-data understanding, yield-target construction, and business problem framing. The revised system keeps the farmer-planning purpose but uses district-crop-season-year observations instead of restricting the model to national totals. I learned that increasing the number of rows is only valid when the observational unit remains genuine. Repeated weather joins or repeated weekly prices against one seasonal yield would create misleading records.",
        "I worked with production, extent, and production values to calculate yield in tonnes per hectare. I also considered how district-level records can be matched to weather locations without using the same season's realised production as a feature. This made the relationship between data availability, leakage, and the decision date clearer.",
        "The main lesson was that a larger raw file is not automatically a better model dataset. The final yield table keeps valid district records and documents the filters that remove totals, invalid extent values, and unmatched weather locations. I would next improve the system with more district-specific agronomic variables and review the revised stakeholder scope before submission."
    ),
    "04_Personal_Learning_Journey_IT24100533_REVISED.docx": (
        "IT24100533 - Danthanarayana D.M.R",
        "My responsibility was weather data, location validation, and forecast-time preparation. In the revised yield system, weather is matched to a district location and summarised over the three complete months before the crop-planning date. The model therefore uses weather that could have been available at the decision point rather than future observations.",
        "I learned that location matching is as important as date matching. District names in the production file required documented normalisation before they could be joined to the location table. I also used a minimum completeness rule so that a yield row is not retained with an unreliable weather window.",
        "The most important learning was that a repeated weather table must not be mistaken for new yield observations. Each district-crop-season-year remains one independent target record. If the project continues, I would add more local weather and soil variables and obtain stakeholder confirmation that the district-level scope is useful."
    ),
    "05_Personal_Learning_Journey_IT24101090_REVISED.docx": (
        "IT24101090 - JAYAKODY N.D",
        "My responsibility was Colombo wholesale-price preparation, price EDA, and target construction. The revised price task predicts the mean wholesale price in the following calendar week from a genuine crop-date observation. This preserves the weekly information instead of collapsing every observation into one monthly value.",
        "I learned to separate wholesale data from retail data, standardise crop names, and handle missing calendar weeks carefully. The daily Colombo workbook provides current price, lag, rolling-average, and rolling-volatility features. All rolling features are built from information available before the target week.",
        "The revised price result is better than the earlier monthly result, but it is still not a guarantee of market price. The data are Colombo/Pettah observations and end in 2025, so the application shows a freshness warning. My main lesson is that correct temporal alignment and honest market coverage are more important than simply increasing the row count."
    ),
    "06_Personal_Learning_Journey_IT23361690_REVISED.docx": (
        "IT23361690 - Gunathilake B.M.P",
        "My responsibility was model training, evaluation, and prediction integration. The revised project uses separate pipelines for next-week Colombo price and district crop yield because the two targets have different observational units and different sources of variation. The Streamlit application still presents both as one farmer decision-support interface.",
        "I compared a dummy baseline, Ridge Regression, Random Forest, and Gradient Boosting using chronological train, validation, and test periods. Gradient Boosting was selected for price and Random Forest for yield. The price model achieved a positive test R2 and beat the persistence baseline, but the result remains uncertain because market prices are volatile.",
        "I learned that a model should not be judged only by whether it runs. Baseline comparison, time-aware validation, data freshness, and clear limitations are equally important. The application therefore warns users that historical Colombo data do not represent a live national price and that yield predictions should support, not replace, agricultural judgement."
    ),
}


def build_personal(filename, identity, p1, p2, p3):
    doc = Document()
    set_a4(doc.sections[0])
    style_doc(doc)
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("IT3091 Machine Learning Personal Learning Journey")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(identity + "\nGroup 2026-AI-16\nRevised project: Colombo next-week wholesale price and district crop yield prediction")
    doc.add_paragraph(p1)
    doc.add_paragraph(p2)
    doc.add_paragraph(p3)
    doc.add_paragraph("AI-use note: This account must be reviewed and approved by the named student before final submission. The group remains responsible for the data, code, experiments, and claims.")
    target = OUT / filename
    doc.save(target)
    return target


if __name__ == "__main__":
    paths = [build_main_report()]
    for filename, values in PERSONAL.items():
        paths.append(build_personal(filename, *values))
    for path in paths:
        print(path)
