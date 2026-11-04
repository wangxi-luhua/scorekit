import json
from pydantic import BaseModel,Field,ConfigDict,ValidationError
import logging
import sys
import argparse
import asyncio

class Stats(BaseModel):
    avg_logical: float
    avg_structural: float
    total_lines: int
    valid_count: int

class Score(BaseModel):
    model_config =ConfigDict(strict=True)
    method:str
    logical:float = Field(ge=0.0,le=100.0)
    structural:float = Field(ge=0.0,le=100.0)

log = logging.getLogger(__name__)





def validate_file(path :str)-> Stats:
    total_logical_scores = 0.0
    total_structural_scores = 0.0
    total_lines = 0
    valid_count = 0
    with open(path,encoding="utf-8") as f:
        log.debug("开始处理数据")
        for i,line in enumerate(f,1):
            if not line.strip():
                    continue
            log.debug("第%s行数据:%r",i,line)
            total_lines += 1
            try:
                row = json.loads(line)
                d = Score(**row)
                
                total_logical_scores += d.logical
                total_structural_scores += d.structural
                valid_count += 1
            except ValidationError as e:
                
                log.warning("第%s行错误:%r,错误原因：%s",i,line,e)
                continue
            except json.JSONDecodeError as e:
                
                log.warning("第%s行JSON解析错误:%r,错误原因：%s",i,line,e)
                continue
        
        log.debug("------------------------------------------")
        log.info("总共%s行数据，%s行数据有效",total_lines,valid_count)
        if valid_count ==0:
            log.error("没有有效数据")
            avg_logical = 0.0
            avg_structural = 0.0
        else:
            avg_logical = total_logical_scores/valid_count
            avg_structural = total_structural_scores/valid_count
   
            log.info("逻辑平均分是%.2f",avg_logical)
            log.info("结构平均分是%.2f",avg_structural)

        
    return Stats(avg_logical=avg_logical,
                    avg_structural=avg_structural,
                    total_lines=total_lines,
                    valid_count=valid_count)


async def check_one(path):
    return await asyncio.to_thread(validate_file,path)

async def run_all(paths):
    return await asyncio.gather(*(check_one(p) for p in paths))

def main():
    parser = argparse.ArgumentParser(description="论文分数校验器：读 jsonl，逐条 pydantic 校验，输出合格率与平均分")
    parser.add_argument("--input",nargs="+",default=["data/scores.jsonl"],help = "输入jsonl文件路径,可多个")
    parser.add_argument("--level",default="INFO",choices=["DEBUG","INFO","WARNING","ERROR"],help = "日志级别,默认INFO")
    parser.add_argument("--logfile",default="app.log",help = "日志文件路径,默认app.log")
    args = parser.parse_args()

    log.setLevel(args.level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    file_handler = logging.FileHandler(args.logfile,encoding="utf-8")
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler.setFormatter(fmt)
    console_handler.setFormatter(fmt)
    log.addHandler(file_handler)
    log.addHandler(console_handler)

    try:
        results = asyncio.run(run_all(args.input))
        

    except FileNotFoundError as e:
        log.error("文件未找到: %s", e)
        sys.exit(1)

    for path,s in zip(args.input,results):
        log.info("%s -> 共%s行，%s行有效，逻辑均分%.2f，结构均分%.2f",
                 path, s.total_lines, s.valid_count, s.avg_logical, s.avg_structural)
    if any(r.valid_count == 0 for r in results):
        sys.exit(1)
if __name__ == "__main__":
    main()
   
    

