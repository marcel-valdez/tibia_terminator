#!/usr/bin/env python3.8
"""Script to produce character auction reports in .csv format."""

import asyncio
import os
import re
import time

from typing import Optional

import argparse
import requests
import tibiapy
from tibiapy import Client

MELEE_SKILLS = ['sword', 'axe', 'club']
USEFUL_SKILLS = ['magic', 'distance', 'sword', 'axe', 'club']

parser = argparse.ArgumentParser(
    description='Tibia auction history report generator.')
parser.add_argument('output_file',
                    help='File onto which to print the report',
                    default='auctions.csv')
parser.add_argument('--page_start',
                    help='Page number at which to start processing',
                    type=int,
                    default=1)
parser.add_argument('--page_count',
                    help='Number of character pages to process',
                    type=int,
                    default=10000)


def debug(msg):
    if os.environ.get('DEBUG') is not None:
        print(msg)


def get_character(name):
    """Fetch a character using requests instead of aiohttp."""
    url = tibiapy.Character.get_url(name)

    r = requests.get(url)
    content = r.text
    character = tibiapy.Character.from_content(content)
    return character


async def get_character_auction_history(
        page_start: int = 1, total_pages: int = 10000
):
    """Fetch the auction history from tibia.com."""
    auction_pages = []
    client = Client()
    response = await client.fetch_auction_history()
    first_auction_page = response.data
    auction_pages.append(first_auction_page)
    print("Fetching first page")
    if first_auction_page.total_pages < total_pages:
        total_pages = first_auction_page.total_pages

    auctions = []
    try:
        for i in range(page_start, page_start + total_pages):
            print(f'Fetching page {i} of {total_pages}')
            response = await client.fetch_auction_history(page=i)
            for auction_entry in response.data.entries:
                # TODO: Add auction_end and auction_start to CSV results
                #       in order to be able to analyze prices over time.
                auction = {
                    'id': auction_entry.auction_id,
                    'name': auction_entry.name,
                    'level': auction_entry.level,
                    'world': auction_entry.world,
                    'vocation': auction_entry.vocation,
                    'sex': auction_entry.sex,
                    'bid': auction_entry.bid,
                    'status': auction_entry.status,
                    'char_url': auction_entry.character_url,
                    'auction_url': auction_entry.url,
                    'start': auction_entry.auction_start,
                    'end': auction_entry.auction_end
                }
                debug(f"Fetching skills for {auction_entry.name}")
                skills = extract_skills_from_sales_argument(
                    auction_entry.sales_arguments)
                if len(skills.keys()) > 0:
                    debug(f"  Found skills: {skills.keys()}")
                    auction.update(skills)
                    auctions.append(auction)
                else:
                    debug("  No skills advertised, ignoring character.")

            time.sleep(0.25)
    except Exception as e:
        print(str(e))
        print("Will attempt to produce CSV with incomplete auction list.")

    return auctions


def extract_skills_from_sales_argument(sales_arguments):
    skills = {'magic': 1, 'distance': 13, 'melee': 13}
    updated = False
    melee = 0
    for sales_argument in sales_arguments:
        content = sales_argument.content
        m = re.match('([0-9]+) Magic Level.*', content)
        if m is not None:
            updated = True
            skills['magic'] = int(m.group(1))
        m = re.match('([0-9]+) Distance Fighting.*', content)
        if m is not None:
            updated = True
            skills['distance'] = int(m.group(1))
        m = re.match('([0-9]+) (Axe|Club|Sword) Fighting.*', content)
        if m is not None:
            updated = True
            other_melee = int(m.group(1))
            if other_melee > melee:
                melee = other_melee
    if melee > 0:
        skills['melee'] = melee

    if updated:
        return skills
    else:
        return {}


async def get_auction_skills(client, auction_id):
    response = await client.fetch_auction(auction_id)
    print('response', response)
    print('response.to_json', response.to_json())
    print('dir(response)', dir(response))
    print('response.__dict__', response.__dict__)
    print('response.keys', response.keys())
    print('response["data"]', response['data'])
    if response.data is None:
        return {}
    print('response.data', response.data)
    # print('dir(response.data)', dir(response.data))
    # print('response.data.__dict___', response.data.__dict__)
    return response.data.skills


def auctions_to_csv(auctions, filename, write_header=True):
    """Write auction objects as CSV entries to a file."""
    print(f"Writing {len(auctions)} auctions to {filename}.")
    keys = [
        'id', 'name', 'level', 'world', 'vocation', 'sex', 'bid', 'status',
        'start', 'end', 'char_url', 'auction_url', 'magic', 'distance', 'melee'
    ]
    with open(filename, "a") as file:
        if write_header:
            file.write(','.join(keys) + '\n')
        for auction in auctions:
            file.write(','.join(map(lambda key: str(auction[key]), keys)) +
                       '\n')


async def main(output_file: str, page_start: Optional[int], page_count: Optional[int]):
    auctions = await get_character_auction_history(page_start, page_count)
    auctions_to_csv(auctions, output_file, page_start == 1)


if __name__ == "__main__":
    args = parser.parse_args()
    asyncio.run(main(args.output_file, args.page_start, args.page_count))
