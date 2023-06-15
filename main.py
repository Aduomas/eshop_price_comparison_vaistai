from crawler_manager import run_app
from mailer import Mailer

if __name__ == "__main__":
    run_app()
    mailer = Mailer()
    mailer.send_reports()
    print("All done!")
