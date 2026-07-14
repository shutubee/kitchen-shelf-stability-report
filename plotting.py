import matplotlib.pyplot as plt
from PIL import Image, ImageDraw


def overlay_members_on_image(image, members, colors):
    img = image.copy().convert("RGB")
    draw = ImageDraw.Draw(img)
    for member, color in zip(members, colors):
        draw.line((member["x1"], member["y1"], member["x2"], member["y2"]), fill=color, width=5)
        mx = (member["x1"] + member["x2"]) / 2
        my = (member["y1"] + member["y2"]) / 2
        draw.text((mx + 4, my + 4), member["id"], fill=color)
    return img


def make_stress_slenderness_plot(df):
    fig, ax = plt.subplots(figsize=(7, 5))
    color_map = {"green": "green", "amber": "orange", "red": "red"}
    for _, row in df.iterrows():
        ax.scatter(row["slenderness"], row["normalized_stress"], color=color_map.get(row["risk_band"], "blue"))
        ax.annotate(row["id"], (row["slenderness"], row["normalized_stress"]), fontsize=8)
    ax.set_xlabel("Slenderness λ")
    ax.set_ylabel("Normalized stress σ / σref")
    ax.set_title("Stress–Slenderness Map")
    ax.grid(True, alpha=0.3)
    return fig


def make_capacity_plot(df):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(df["id"], df["knockdown_capacity_kN"])
    ax.set_ylabel("Imperfection-adjusted capacity (kN)")
    ax.set_title("Member capacity")
    ax.grid(True, axis="y", alpha=0.3)
    return fig


def make_risk_bar_plot(df):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(df["id"], df["risk_score"])
    ax.set_ylabel("Composite risk score")
    ax.set_title("Member Risk Scores")
    ax.grid(True, axis="y", alpha=0.3)
    return fig