#!/usr/bin/env python
"""
    cv2
    ~~~

    Your resume: hosted, git-branched, simply.
"""

import os
import shutil
import tempfile
from pygit2 import clone_repository, Repository, GitError
from wtforms import fields, validators
from flask import Flask, request, redirect, url_for, render_template, flash, abort
from flask.ext.wtf import Form
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)

app.config.update(SQLALCHEMY_DATABASE_URI=os.environ['SQLALCHEMY_DATABASE_URI'],
                  SECRET_KEY='so-secure')

db = SQLAlchemy(app)


class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    remote = db.Column(db.String)


class AccountForm(Form):
    remote = fields.TextField('Remote', validators=[validators.DataRequired()])


@app.route('/')
def hello():
    return "hey"


@app.route('/<username>', methods=['GET', 'POST'])
def settings(username):
    account = Account.query.filter_by(username=username).first() or Account(username=username)
    form = AccountForm(request.form, account)
    if form.validate_on_submit():
        account.remote = form.remote.data
        db.session.add(account)
        db.session.commit()
        flash('saved')
    return render_template('settings.html', username=username, form=form)


@app.route('/<branch>/', subdomain='<username>')
@app.route('/<branch>/<path:filename>', subdomain='<username>')
@app.route('/resume/<username>/<branch>/')
@app.route('/resume/<username>/<branch>/<path:filename>')
def resume(username, branch, filename='index.html'):
    account = Account.query.filter_by(username=username).first() or abort(404)
    try:
        repo_dir = tempfile.mkdtemp()
        try:
            repo = clone_repository(account.remote, repo_dir, bare=True)
        except GitError:
            abort(404)
        # try:
        #     repo = Repository(account.remote)
        # except KeyError:
        #     abort(404)
        branch = repo.lookup_branch(branch) or abort(404)
        tree = branch.get_object().tree
        try:
            entry = tree[filename]
        except KeyError:
            abort(404)
        blob = repo.get(entry.hex)
        return blob.data
    finally:
        shutil.rmtree(repo_dir)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
