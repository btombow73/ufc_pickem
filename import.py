import csv
import sys
import os
from ufc_pickem.app import create_app, db  # Absolute import
from ufc_pickem.models import Fighter  # Assuming your model is named Fighter

# Add the ufc_pickem folder to the Python path (if running this outside the package structure)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'ufc_pickem')))

# Create the Flask app
app = create_app()

# Use app context for the database operations
with app.app_context():
    # Path to your CSV file
    csv_file_path = 'fighters.csv'

    # Clear the existing data in the 'fighters' table
    try:
        Fighter.query.delete()  # Deletes all records in the table
        db.session.commit()  # Commit the deletion
        print("Existing data deleted successfully.")
    except Exception as e:
        print(f"Error while deleting data: {e}")
        db.session.rollback()

    # Open and read the CSV file with the correct encoding
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            csvreader = csv.DictReader(csvfile)

            # Loop through each row in the CSV file
            for row in csvreader:
                # Create a Fighter object using data from the CSV row
                fighter = Fighter(
                    name=row.get('Name', 'N/A'),
                    nickname=row.get('Nickname', 'N/A'),
                    weight_class=row.get('Weight Class', 'N/A'),
                    record=row.get('Record', 'N/A'),
                    knockouts=row.get('Knockouts', '0'),
                    submissions=row.get('Submissions', '0'),
                    first_round_finishes=row.get('First Round Finishes', '0'),
                    takedown_accuracy=row.get('Takedown Accuracy', 'N/A'),
                    striking_accuracy=row.get('Striking Accuracy', 'N/A'),
                    sig_str_landed_total=row.get('Sig Str Landed Total', '0'),
                    sig_str_attempted_total=row.get('Sig Str Attempted Total', '0'),
                    takedowns_landed_total=row.get('Takedowns Landed Total', '0'),
                    takedowns_attempted_total=row.get('Takedowns Attempted Total', '0'),
                    sig_strikes_per_min=row.get('Sig Strikes Per Min', '0'),
                    takedown_avg_per_min=row.get('Takedown Avg Per Min', '0'),
                    sig_str_def=row.get('Sig Str Def', 'N/A'),
                    knockdown_avg=row.get('Knockdown Avg', '0'),
                    sig_strikes_absorbed_per_min=row.get('Sig Strikes Absorbed Per Min', '0'),
                    sub_avg_per_min=row.get('Sub Avg Per Min', '0'),
                    takedown_def=row.get('Takedown Def', 'N/A'),
                    avg_fight_time=row.get('Avg Fight Time', '0'),
                    sig_strikes_while_standing=row.get('Sig Strikes While Standing', '0'),
                    sig_strikes_while_clinched=row.get('Sig Strikes While Clinched', '0'),
                    sig_strikes_while_grounded=row.get('Sig Strikes While Grounded', '0'),
                    win_by_ko_tko=row.get('Win by KO/TKO', '0'),
                    win_by_decision=row.get('Win by Decision', '0'),
                    win_by_submission=row.get('Win by Submission', '0'),
                    image_url=row.get('Image URL', 'N/A')
                )

                # Add the Fighter object to the session
                db.session.add(fighter)

            # Commit the session to the database
            db.session.commit()
            print("Data imported successfully!")

    except Exception as e:
        print(f"Error while importing data: {e}")
        db.session.rollback()
