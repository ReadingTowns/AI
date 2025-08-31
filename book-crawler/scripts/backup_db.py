#!/usr/bin/env python3
"""
데이터베이스 백업 스크립트
자동 백업 및 복구 기능 제공
"""

import os
import sys
import subprocess
from datetime import datetime
import shutil
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

class DatabaseBackup:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # DB 연결 정보
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'book_db_test'),
            'port': os.getenv('DB_PORT', '3306')
        }
        
    def create_backup(self, backup_type="manual"):
        """MySQL 데이터베이스 백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{self.db_config['database']}_{backup_type}_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # mysqldump 명령어 구성
            cmd = [
                'mysqldump',
                f'-h{self.db_config["host"]}',
                f'-u{self.db_config["user"]}',
                f'-P{self.db_config["port"]}',
                '--single-transaction',  # InnoDB 테이블 일관성 보장
                '--quick',  # 대용량 테이블 처리
                '--lock-tables=false',  # 테이블 잠금 방지
                '--routines',  # 저장 프로시저/함수 포함
                '--triggers',  # 트리거 포함
                self.db_config['database']
            ]
            
            # 비밀번호가 있으면 추가
            if self.db_config['password']:
                cmd.append(f'-p{self.db_config["password"]}')
            
            # 백업 실행
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
                
            if result.returncode != 0:
                logger.error(f"백업 실패: {result.stderr}")
                return None
                
            # 백업 파일 압축
            compressed_path = backup_path.with_suffix('.sql.gz')
            subprocess.run(['gzip', str(backup_path)])
            
            # 백업 메타데이터 저장
            metadata = {
                'timestamp': timestamp,
                'type': backup_type,
                'database': self.db_config['database'],
                'file': str(compressed_path.name),
                'size': os.path.getsize(compressed_path)
            }
            
            metadata_file = self.backup_dir / 'backup_metadata.json'
            metadata_list = []
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata_list = json.load(f)
            
            metadata_list.append(metadata)
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata_list, f, indent=2, ensure_ascii=False)
            
            logger.info(f"백업 성공: {compressed_path}")
            
            # 오래된 백업 삭제 (7일 이상)
            self.cleanup_old_backups(days=7)
            
            return compressed_path
            
        except Exception as e:
            logger.error(f"백업 중 오류 발생: {str(e)}")
            return None
    
    def restore_backup(self, backup_file):
        """백업 파일로부터 데이터베이스 복구"""
        try:
            backup_path = self.backup_dir / backup_file
            
            if not backup_path.exists():
                logger.error(f"백업 파일을 찾을 수 없습니다: {backup_file}")
                return False
            
            # 압축 해제
            if backup_path.suffix == '.gz':
                subprocess.run(['gunzip', '-k', str(backup_path)])
                sql_path = backup_path.with_suffix('')
            else:
                sql_path = backup_path
            
            # 복구 전 현재 상태 백업
            logger.info("복구 전 현재 상태를 백업합니다...")
            self.create_backup(backup_type="before_restore")
            
            # MySQL 복구 명령어
            cmd = [
                'mysql',
                f'-h{self.db_config["host"]}',
                f'-u{self.db_config["user"]}',
                f'-P{self.db_config["port"]}',
                self.db_config['database']
            ]
            
            if self.db_config['password']:
                cmd.append(f'-p{self.db_config["password"]}')
            
            # 복구 실행
            with open(sql_path, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
            
            # 임시 파일 삭제
            if backup_path.suffix == '.gz' and sql_path.exists():
                os.remove(sql_path)
            
            if result.returncode != 0:
                logger.error(f"복구 실패: {result.stderr}")
                return False
            
            logger.info(f"복구 성공: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"복구 중 오류 발생: {str(e)}")
            return False
    
    def cleanup_old_backups(self, days=7):
        """오래된 백업 파일 삭제"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for backup_file in self.backup_dir.glob("backup_*.sql.gz"):
            # 파일명에서 날짜 추출
            try:
                date_str = backup_file.stem.split('_')[3]  # YYYYMMDD 부분
                file_date = datetime.strptime(date_str[:8], "%Y%m%d")
                
                if file_date < cutoff_date:
                    os.remove(backup_file)
                    logger.info(f"오래된 백업 삭제: {backup_file.name}")
            except:
                continue
    
    def list_backups(self):
        """사용 가능한 백업 목록 표시"""
        metadata_file = self.backup_dir / 'backup_metadata.json'
        
        if not metadata_file.exists():
            print("백업이 없습니다.")
            return
        
        with open(metadata_file, 'r') as f:
            backups = json.load(f)
        
        print("\n사용 가능한 백업:")
        print("-" * 60)
        
        for idx, backup in enumerate(backups[-10:], 1):  # 최근 10개만 표시
            size_mb = backup['size'] / (1024 * 1024)
            print(f"{idx}. {backup['file']}")
            print(f"   날짜: {backup['timestamp']}")
            print(f"   타입: {backup['type']}")
            print(f"   크기: {size_mb:.2f} MB")
            print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='데이터베이스 백업 관리')
    parser.add_argument('action', choices=['backup', 'restore', 'list'], 
                       help='수행할 작업')
    parser.add_argument('--file', help='복구할 백업 파일명')
    parser.add_argument('--type', default='manual', 
                       help='백업 타입 (manual/auto/scheduled)')
    
    args = parser.parse_args()
    
    backup_manager = DatabaseBackup()
    
    if args.action == 'backup':
        backup_manager.create_backup(backup_type=args.type)
    elif args.action == 'restore':
        if not args.file:
            backup_manager.list_backups()
            print("\n복구할 파일을 --file 옵션으로 지정하세요.")
        else:
            backup_manager.restore_backup(args.file)
    elif args.action == 'list':
        backup_manager.list_backups()

if __name__ == "__main__":
    main()