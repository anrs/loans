#!/usr/bin/env python
import decimal

import mock
from nose import tools

import loans

@mock.patch("loans.read_loans_file", return_value=iter([
            "MSISDN,Network,Date,Product,Amount",
            "27729554427,'Network 1','12-Mar-2016','Loan Product 1',1000.00",
            "MSISDN,Network,Date,Product,Amount",
            "27722342551,'Network 2','16-Mar-2016','Loan Product 1',1122.00",
            "MSISDN,Network,Date,Product,Amount",
            "27725544272,'Network 3','17-Mar-2016','Loan Product 2',2084.00",
            # invalid line
            "27722342551,'Network 3','17-Mar-2016','Loan Product 3',,2084.00",
]))
def test_load_loans(read_loans_file):
    loan_list = list(loans.load_loans("faked"))
    tools.ok_(loan_list)
    tools.ok_(all(loan_list))
    tools.eq_(3, len(loan_list))
    tools.ok_(all(isinstance(loan.msisdn, int) for loan in loan_list))
    tools.ok_(all(isinstance(loan.amount, decimal.Decimal) for loan in loan_list))
    tools.eq_([1, 2, 3], [loan.get_network_id() for loan in loan_list])
    tools.eq_([1, 1, 2], [loan.get_product_id() for loan in loan_list])
    tools.eq_([201603, 201603, 201603], [loan.get_date_index() for loan in loan_list])

@mock.patch("loans.read_loans_file", return_value=iter([
            # following 6 lines are invalid.
            "a,'Network 1','12-Mar-2016','Loan Product 1',1000.00",
            "27722342551,'Network b','16-Mar-2016','Loan Product 1',1122.00",
            "27722342551,'Network 3','32-Mar-2016','Loan Product 2',2084.00",
            "27722342551,'Network 3','17-Mar-2016','Loan Product 2',a",
            "27722342551,'Network 3','17-Mar-2016','Loan Product a',2084.00",
            # two valid lines.
            "27722342551,'Network 3','17-Mar-2016','Loan Product 3',-2084.00",
            "27722342551,'Network 3','17-Mar-2016','Loan Product 3',2084.00",
]))
def test_loan_format(read_loans_file):
    loan_list = list(loans.load_loans("faked"))
    tools.ok_(loan_list)
    tools.ok_(all(loan_list))
    tools.eq_(2, len(loan_list))

@mock.patch("loans.read_loans_file", return_value=iter([
            "27729554427,'Network 1','12-Mar-2016','Loan Product 1',1000.00",
            "27729554427,'Network 1','15-Mar-2016','Loan Product 1',1000.00",
            "27729554427,'Network 1','12-Feb-2016','Loan Product 1',1000.00",
            "27729554427,'Network 1','15-Feb-2016','Loan Product 1',1122.00",
            "27722342551,'Network 1','16-Mar-2016','Loan Product 2',1122.00",
            "27725544272,'Network 3','17-Mar-2016','Loan Product 3',2084.00",
            "27725544272,'Network 3','18-Mar-2016','Loan Product 3',-84.00",
]))
def test_loans_add(load_loans):
    store = loans.Loans()
    for loan in loans.load_loans("faked"):
        store.add_loan(loan)
    tools.ok_(store.summing)
    tools.eq_(4, len(store.summing))
    tools.eq_((decimal.Decimal(2000.00), 2), store.summing.get((201603, 1, 1)))
    tools.eq_((decimal.Decimal(2122.00), 2), store.summing.get((201602, 1, 1)))
    tools.eq_((decimal.Decimal(1122.00), 1), store.summing.get((201603, 1, 2)))
    tools.eq_((decimal.Decimal(2000.00), 2), store.summing.get((201603, 3, 3)))
