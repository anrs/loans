#!/usr/bin/env python
import datetime
import decimal
import logging
import logging.config
import os
import operator
import re
import sys
import tempfile

logging.config.fileConfig("logging.ini")
logger = logging.getLogger(__name__)

FIELDS = ["msisdn", "network", "date", "product", "amount"]

class Loan(object):

    raw_network_re = re.compile(r"^.*?(?i)network\s+(\d+).*$")
    raw_product_re = re.compile(r"^.*?(?i)loan product\s+(\d+).*$")
    raw_date_re = re.compile(r"[-\w]+")

    def __init__(self, msisdn, network, date, product, amount):
        self.msisdn = msisdn
        self.network = network
        self.date = date
        self.product = product
        self.amount = amount
        self.network_id = None
        self.product_id = None

    def format_msisdn(self):        
        if isinstance(self.msisdn, int):
            return True

        if isinstance(self.msisdn, basestring):
            msisdn = str(self.msisdn)
            if msisdn.isdigit():
                self.msisdn = int(msisdn)
                return True

        return False

    def format_network(self):
        if self.network_id is not None:
            return True
        
        match = self.raw_network_re.search(self.network)
        if not match:
            return False

        self.network_id = int(match.group(1))
        return True
    
    def format_product(self):
        if self.product_id is not None:
            return True
        
        match = self.raw_product_re.search(self.product)
        if not match:
            return False

        self.product_id = int(match.group(1))
        return True

    def format_date(self):
        if isinstance(self.date, datetime.datetime):
            return True

        match = self.raw_date_re.search(self.date)
        if not match:
            logging.error("invalid Loan.date: %s", self.date)
            return False
        self.date = match.group(0)
        
        try:
            self.date = datetime.datetime.strptime(self.date, "%d-%b-%Y")
        except ValueError:
            logger.exception("invalid Loan.date: %s", self.date)
            return False
        else:
            return True
    
    def format_amount(self):
        if isinstance(self.amount, decimal.Decimal):
            return True

        try:
            self.amount = decimal.Decimal(self.amount)
        except Exception:
            logger.exception("invalid Loan.amount: %s", self.amount)
            return False
        
        return True

    def format(self):
        formats = [self.format_msisdn,
                   self.format_network,
                   self.format_date,
                   self.format_product,
                   self.format_amount]
        return all(format() for format in formats)

    def get_product_id(self):
        return self.product_id

    def get_network_id(self):
        return self.network_id

    def get_date_index(self):
        return int(self.date.strftime("%Y%m"))

    @classmethod
    def parse_line(cls, line):
        # Unexpected fields length.
        fields = line.split(",")
        if len(fields) != len(FIELDS):
            logger.error("invalid loan line: %s", line)
            return
        
        # Check the line if is a headline.
        if fields[0].lower() == FIELDS[0]:
            logger.debug("loan headline: %s", line)
            return
        
        try:
            loan = Loan(*fields)
            if not loan.format():
                logger.error("invalid loan line: %s", line)
                return
        except Exception:
            logger.exception("invalid loan line: %s", line)
            return
        else:
            return loan


class Loans(object):

    default = (decimal.Decimal(0), 0)

    def __init__(self):
        self.summing = {}

    def generate_summing_key(self, loan):
        return (loan.get_date_index(), loan.get_network_id(), loan.get_product_id())

    @classmethod
    def format_summing_line(cls, key, value):
        date_index, network_id, product_id = key
        amount, count = value
        date = datetime.datetime.strptime(str(date_index), "%Y%m")
        return "'Network %s','Loan Product %s','%s',%s,%s" % (
            network_id, product_id, date.strftime("%b-%Y"), amount, count
        )

    @classmethod
    def format_summing_headline(cls):
        return "Network,Product,Month,Amount,Count"

    def iter_sorted_summing(self):
        summing_list = sorted(self.summing.items(), key=operator.itemgetter(0))
        for key, value in summing_list:
            yield key, value

    def output(self, filepath):
        fd, temp_filepath = tempfile.mkstemp()
        os.close(fd)
        with open(temp_filepath, "w") as f:
            # Print a headline first.
            print >>f, self.format_summing_headline()

            for key, value in self.iter_sorted_summing():
                line = self.format_summing_line(key, value)
                print >>f, line

        if os.path.exists(filepath):
            logger.error("output file %s is exists, but %s is remained",
                         filepath, temp_filepath)
            return False

        try:
            os.rename(temp_filepath, filepath)
        except Exception:
            logging.exception("failed to mv %s to %s", temp_filepath, filepath)
            return False
        else:
            logging.info("%s is done.", filepath)
            return True
    
    def add_loan(self, loan):
        key = self.generate_summing_key(loan)
        amount, count = self.summing.setdefault(key, self.default)
        self.summing[key] = (amount+loan.amount, count+1)

        
def read_loans_file(filepath):
    try:
        with open(filepath) as f:
            for line in f:
                # Remove the endswith whitespaces and commas.
                yield line.strip(" ,")
    except Exception:
        logging.exception("failed to read loans file: %s", filepath)
        raise

def load_loans(filepath):
    for line in read_loans_file(filepath):
        loan = Loan.parse_line(line)
        if loan is not None:
            yield loan
 
def main(src, dest):
    loans = Loans()
    for loan in load_loans(src):
        loans.add_loan(loan)
    else:
        loans.output(dest)
    return 0

usage = """\
python loans.py <loans file> [, <Output.csv>]
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print >>sys.stderr, usage
        sys.exit(1)
        
    src = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) >= 3 else "Output.csv"
    try:
        sys.exit(main(src, dest))
    except Exception:
        sys.exit(1)
