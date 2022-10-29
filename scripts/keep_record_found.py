import keep_sync as keep
import argparse
import os
import requests
import datetime
import time

RUN_LOG_API = "https://api.gotokeep.com/pd/v3/runninglog/{run_id}"
# RUN_LOG_API = "https://api.gotokeep.com/pd/v3/hikinglog/{run_id}"
RUN_DATA_API = "https://api.gotokeep.com/pd/v3/stats/detail?dateUnit=all&type=running&lastDate={last_date}"


# RUN_DATA_API = "https://api.gotokeep.com/pd/v3/stats/detail?dateUnit=all&type=hiking&lastDate={last_date}"


def get_to_download_working_ids(session, headers, last_date, url):
  # last_date = 0
  result = []
  if len(url) == 0:
    url = RUN_DATA_API
  r = session.get(url.format(last_date=last_date), headers=headers)
  if r.ok:
    run_logs = r.json()["data"]["records"]

    for i in run_logs:
      logs = [j["stats"] for j in i["logs"]]
      result.extend(k["id"] for k in logs if not k is None and not k["isDoubtful"])
  return result


def get_single_run_data(session, headers, run_id):
  r = session.get(RUN_LOG_API.format(run_id=run_id), headers=headers)
  if r.ok:
    return r.json()


def create_gpx(email, password):
  if not os.path.exists(keep.GPX_FOLDER):
    os.mkdir(keep.GPX_FOLDER)
  s = requests.Session()
  s, headers = keep.login(s, email, password)
  last_date = 1665763200000
  record_id_list = get_to_download_working_ids(s, headers, last_date, "")
  for record_id in record_id_list:
    data = get_single_run_data(s, headers, record_id)
    # 生成 GPX
    keep.parse_raw_data_to_nametuple(data, [], True)


def deal_hiking(email, password):
  HIKING_DATA_API = "https://api.gotokeep.com/pd/v3/stats/detail?dateUnit=all&type=hiking&lastDate={last_date}"
  HIKING_LOG_API = "https://api.gotokeep.com/pd/v3/hikinglog/{run_id}"
  session = requests.Session()
  session, headers = keep.login(session, email, password)
  result = []
  res = session.get(HIKING_DATA_API.format(last_date=0), headers=headers)
  if res.ok:
    run_logs = res.json()["data"]["records"]

    for i in run_logs:
      logs = [j["stats"] for j in i["logs"]]
      result.extend(k["id"] for k in logs
                    if not k is None and not k["isDoubtful"]
                    and k['dataType'] == 'outdoorWalking'
                    and k['distance'] <= 500
                    )
    for record in result:
      r = session.delete(HIKING_LOG_API.format(run_id=record))
      if r.ok:
        print(r.json())


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("phone_number", help="keep login phone number")
  parser.add_argument("password", help="keep login password")
  parser.add_argument(
    "--with-gpx",
    dest="with_gpx",
    action="store_true",
    help="get all keep data to gpx and download",
  )
  options = parser.parse_args()
  email = options.phone_number
  password = options.password
  deal_hiking(email, password)
  print("程序执行完成")
