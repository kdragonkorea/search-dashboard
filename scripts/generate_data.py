import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_dummy_data(num_weeks=10, rows_per_week=100):
    """
    Generates a dummy Excel file with travel search data.
    """
    data = []
    start_date = datetime.now() - timedelta(weeks=num_weeks)
    
    keywords = ["Jeju", "Seoul", "Busan", "Osaka", "Tokyo", "Bangkok", "Danang", "Paris", "London", "New York"]
    failed_keywords = ["asdf", "gagal", "nowhere", "unknown place", "mars"]
    
    for i in range(num_weeks):
        week_start = start_date + timedelta(weeks=i)
        for _ in range(rows_per_week):
            # Random date within the week
            search_date = week_start + timedelta(days=random.randint(0, 6))
            
            # Decide if fit is a successful or failed search
            if random.random() < 0.1: # 10% failure
                keyword = random.choice(failed_keywords)
                result_count = 0
            else:
                keyword = random.choice(keywords)
                result_count = random.randint(1, 50)
            
            user_age = random.choice([20, 30, 40, 50, 60])
            search_attribute = random.choice(["Hotel", "Flight", "Package"])
            
            data.append({
                "search_date": search_date.strftime("%Y-%m-%d"),
                "keyword": keyword,
                "result_count": result_count,
                "user_age": user_age,
                "search_type": search_attribute
            })
            
    df = pd.DataFrame(data)
    file_path = "dummy_data.xlsx"
    df.to_excel(file_path, index=False)
    print(f"Dummy data created at {file_path}")
    return df

if __name__ == "__main__":
    generate_dummy_data()
