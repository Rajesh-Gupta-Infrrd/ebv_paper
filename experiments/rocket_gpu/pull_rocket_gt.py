import os, sys, json, pathlib
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/Users/rajeshgupta/Projects/DocAI/eval/table_extraction/rocket")
import download_docs_rocketuat as D
os.environ["MONGO_CONN_STR"] = D.MONGO_URI
os.environ.setdefault("MONGODB_DB_NAME", "titanDB")
from pymongo import MongoClient
from core_db_encryption import decrypt_wrapper

db = MongoClient(D.MONGO_URI, serverSelectionTimeoutMS=8000)["titanDB"]
EF = db["extraction_field"]
ROOT = pathlib.Path("/Users/rajeshgupta/Git_Clones/research_papers/ebv_paper/experiments/datasets/rocket")
TYPES = ["URLA", "CD_tables", "AUS_DU", "Bank", "CreditReportLender"]

@decrypt_wrapper
def find_fields(collection, query, account_id=None, user_model_id=None):
    return list(collection.find(query))

for typ in TYPES:
    chosen = set(json.load(open(ROOT / typ / "field_list.json"))["fields"])
    outdir = ROOT / typ / "gt"; outdir.mkdir(parents=True, exist_ok=True)
    rids = [p.stem for p in (ROOT / typ / "fields").glob("*.json") if p.stem != "field_list"]

    def one(rid):
        doc = db["document"].find_one({"requestId": rid}, {"customerId": 1, "userModelId": 1}) or {}
        rows = find_fields(EF, {"requestId": rid}, account_id=doc.get("customerId"), user_model_id=doc.get("userModelId"))
        gt = {}
        for r in rows:
            fn = r.get("fieldName")
            if fn not in chosen:
                continue
            cv = r.get("correctedValue")
            # GT = human-corrected value when present, else the extracted value
            gt[fn] = cv if (cv not in (None, "")) else r.get("value")
        if gt:
            json.dump({"requestId": rid, "docType": typ, "gt": gt}, open(outdir / f"{rid}.json", "w"))
            return 1
        return 0

    with ThreadPoolExecutor(max_workers=24) as ex:
        n = sum(ex.map(one, rids))
    print(f"{typ:20} gt_files={n}/{len(rids)}", flush=True)
print("DONE")
