Project
Loans is a solution for parse Loans.csv file. It calculates loans' total amount and count group by network, product and month.

Usage
python loans.py src [, dest]

Requirement
- Python 2.7
- nose (option)
- mock (option)
- pylint (option)
- pyflakes (option)

Implementation
1. The loans.py read a line from Loans.csv at one time, filter out headlines and invalid lines.
2. Convert the line into loans.Loan instance, and format all fields but except invalid fields' values, it means would drop out the loans.Loan instance.
3. The loans.Loans.add_loan() method receives a valid loan instance to calculate (like group by in SQL) it with the original summing, and stores the calculated amount/count backing to the summing.
4. Output content will be sorted by Month, network and product.
