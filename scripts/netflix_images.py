import pandas as pd
import aiohttp
import asyncio
import json
from dotenv import load_dotenv
import os


# CONFIGURATION

load_dotenv()
TMDB_KEY = os.getenv("api")

if not TMDB_KEY:
    raise ValueError("❌ Clé API TMDB introuvable dans .env (clé = api).")

IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


# REQUÊTES TMDB

async def fetch_json(session, url):
    try:
        async with session.get(url) as resp:
            return await resp.json()
    except Exception as e:
        print("Erreur requête :", e)
        return None


async def search_person(session, name):
    url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_KEY}&query={name}"
    data = await fetch_json(session, url)

    if not data or not data.get("results"):
        return None

    profile = data["results"][0].get("profile_path")
    return IMAGE_BASE + profile if profile else None


# TRAITEMENT CAST

async def process_people(input_file, output_file, column_name):
    print(f"\n👥 Traitement {input_file}...\n")

    df = pd.read_excel(input_file)
    df[column_name] = df[column_name].astype(str)

    tasks = []

    async with aiohttp.ClientSession() as session:
        for entry in df[column_name]:
            names = [n.strip() for n in entry.split(",")]
            for name in names:
                tasks.append(process_one_person(session, name))

        results = await asyncio.gather(*tasks)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"✔ {output_file} généré")


async def process_one_person(session, name):
    name = str(name)
    print(f"Nom : {name}")

    url = await search_person(session, name)

    return {
        "name": name,
        "image_url": url
    }


# IMAGE

async def image():
    print("🚀 Début du traitement CAST...\n")

    await process_people(
        input_file="cast.xlsx",
        output_file="cast.json",
        column_name="cast"
    )

    print("\n🎉 Terminé ! cast.json a été généré.")


if __name__ == "__main__":
    asyncio.run(image())
