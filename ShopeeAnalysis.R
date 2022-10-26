setwd("D:/user/桌面")
library(openxlsx)
dataframe_1<- read.csv("Shopee_OLD1.csv")


plot(x=dataframe_1$price,y=dataframe_1$每小時銷售量)


boxplot(dataframe_1$每小時銷售量)

cor(dataframe_1$銷售總量, dataframe_1$salesvolume, method="pearson")
cor.test(dataframe_1$銷售總量, dataframe_1$每小時銷售量, method="pearson")

summary(dataframe_1)


require(ggplot2)
ggplot(data=dataframe_1) +                        # 準備畫布
  geom_point(aes(x=`每小時銷售量`,           # 散布圖
                 y=`銷售總量`)) +
  theme_bw()



