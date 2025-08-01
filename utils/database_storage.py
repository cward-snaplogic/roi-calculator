"""
Database storage utilities for persisting ROI calculator inputs
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
load_dotenv()

class ROIStorage:
    def __init__(self):
        self.connection = None
        self._connect()

    def _connect(self):
        """Establish database connection"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                self.connection = psycopg2.connect(database_url)
            else:
                self.connection = psycopg2.connect(
                    host=os.getenv('PGHOST'),
                    database=os.getenv('PGDATABASE'),
                    user=os.getenv('PGUSER'),
                    password=os.getenv('PGPASSWORD'),
                    port=os.getenv('PGPORT')
                )
            self.connection.autocommit = True
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")

    def save_roi_inputs(self, use_case_title: str, inputs: Dict[str, Any], business_unit: str = None) -> bool:
        """Save or update ROI inputs for a use case"""
        try:
            if not self.connection:
                return False

            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO roi_inputs (
                        use_case_title, business_unit, labor_impact_hours, labor_cost_hourly,
                        cost_avoidance_annual, revenue_impact_annual, risk_mitigation_score,
                        customer_reach_score, time_to_value_hours, implementation_cost_hourly,
                        confidence_level, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (use_case_title)
                    DO UPDATE SET
                        business_unit = EXCLUDED.business_unit,
                        labor_impact_hours = EXCLUDED.labor_impact_hours,
                        labor_cost_hourly = EXCLUDED.labor_cost_hourly,
                        cost_avoidance_annual = EXCLUDED.cost_avoidance_annual,
                        revenue_impact_annual = EXCLUDED.revenue_impact_annual,
                        risk_mitigation_score = EXCLUDED.risk_mitigation_score,
                        customer_reach_score = EXCLUDED.customer_reach_score,
                        time_to_value_hours = EXCLUDED.time_to_value_hours,
                        implementation_cost_hourly = EXCLUDED.implementation_cost_hourly,
                        confidence_level = EXCLUDED.confidence_level,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    use_case_title,
                    business_unit or 'Unknown',
                    float(inputs.get('labor_impact_hours', 0)),
                    float(inputs.get('labor_cost_hourly', 100)),
                    float(inputs.get('cost_avoidance_annual', 0)),
                    float(inputs.get('revenue_impact_annual', 0)),
                    int(inputs.get('risk_mitigation_score', 3)),
                    int(inputs.get('customer_reach_score', 3)),
                    float(inputs.get('time_to_value_hours', 0)),
                    float(inputs.get('implementation_cost_hourly', 100)),
                    int(inputs.get('confidence_level', 3))
                ))
                return True
        except Exception as e:
            return False

    def load_roi_inputs(self, use_case_title: str) -> Optional[Dict[str, Any]]:
        """Load ROI inputs for a specific use case"""
        try:
            if not self.connection:
                return None

            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM roi_inputs WHERE use_case_title = %s
                """, (use_case_title,))

                result = cursor.fetchone()
                if result:
                    return {
                        'labor_impact_hours': float(result['labor_impact_hours']),
                        'labor_cost_hourly': float(result['labor_cost_hourly']),
                        'cost_avoidance_annual': float(result['cost_avoidance_annual']),
                        'revenue_impact_annual': float(result['revenue_impact_annual']),
                        'risk_mitigation_score': int(result['risk_mitigation_score']),
                        'customer_reach_score': int(result['customer_reach_score']),
                        'time_to_value_hours': float(result['time_to_value_hours']),
                        'implementation_cost_hourly': float(result['implementation_cost_hourly']),
                        'confidence_level': int(result['confidence_level'])
                    }
                return None
        except Exception:
            return None

    def load_all_roi_inputs(self) -> Dict[str, Dict[str, Any]]:
        """Load all saved ROI inputs"""
        try:
            if not self.connection:
                return {}

            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM roi_inputs ORDER BY updated_at DESC
                """)

                results = cursor.fetchall()
                roi_inputs = {}

                for result in results:
                    roi_inputs[result['use_case_title']] = {
                        'labor_impact_hours': float(result['labor_impact_hours']),
                        'labor_cost_hourly': float(result['labor_cost_hourly']),
                        'cost_avoidance_annual': float(result['cost_avoidance_annual']),
                        'revenue_impact_annual': float(result['revenue_impact_annual']),
                        'risk_mitigation_score': int(result['risk_mitigation_score']),
                        'customer_reach_score': int(result['customer_reach_score']),
                        'time_to_value_hours': float(result['time_to_value_hours']),
                        'implementation_cost_hourly': float(result['implementation_cost_hourly']),
                        'confidence_level': int(result['confidence_level'])
                    }

                return roi_inputs
        except Exception:
            return {}

    def delete_roi_inputs(self, use_case_title: str) -> bool:
        """Delete ROI inputs for a specific use case"""
        try:
            if not self.connection:
                return False

            with self.connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM roi_inputs WHERE use_case_title = %s
                """, (use_case_title,))

                return cursor.rowcount > 0
        except Exception:
            return False

    def get_saved_use_cases(self) -> List[str]:
        """Get list of use cases with saved ROI inputs"""
        try:
            if not self.connection:
                return []

            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT use_case_title FROM roi_inputs ORDER BY updated_at DESC
                """)

                results = cursor.fetchall()
                return [result[0] for result in results]
        except Exception:
            return []

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()