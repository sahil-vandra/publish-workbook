git add .
git commit -m "message"
git lfs push --all origin main
git push -u origin main
git lfs migrate import --include="*.twbx"