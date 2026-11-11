PHONY: github pudding

github:
	rm -rf docs
	cp -r build docs
	# the no-college and prior check data stay local (see .gitignore)
	rm -rf docs/data/nocollege docs/data/informative docs/data/prior-1 docs/data/prior-uniform
	touch docs/.nojekyll
	git add -A
	git commit -m "update github pages"
	git push

protect:
	cd build && npx staticrypt --short index.html -p $(shell grep PASSWORD .env | cut -d '=' -f2) -d .

staging: 
	npm run build
	make github

production:
	BASE_PATH=/2026/11/wnba-politics npm run build
	rm -rf build/data/nocollege build/data/informative build/data/prior-1 build/data/prior-uniform
	make pudding

aws-sync:
	aws s3 sync build s3://pudding.cool/2026/11/wnba-politics --delete --cache-control 'max-age=31536000'

aws-cache:
	aws cloudfront create-invalidation --distribution-id E13X38CRR4E04D --paths '/2026/11/wnba-politics*'	

pudding: aws-sync aws-cache