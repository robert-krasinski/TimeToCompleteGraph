library(ggplot2)
args <- commandArgs(trailingOnly = TRUE)

dataFile = args[1]

#read csv file
issues <- read.csv(
  file = dataFile,
  head = TRUE,
  sep = ",",
  dec = ".",
  stringsAsFactors = FALSE
)

#identify final statuses for issues
completedStatuses <-
  c("Closed", "Rejected", "Reviewed", 'Completed', 'Resolved', 'Closed')

#convert string to date
issues$movedToComplete <-
  as.POSIXct(issues$movedToComplete, format = "%Y-%m-%dT%H:%M:%S")

#add week column
issues[, "EndWeek"] <-
  as.Date(cut(as.Date(issues$movedToComplete), breaks = "week"))
#this will help us calculate (please let me know if this can be done easier)
issues[, "Quantity"] <- 1

#choose only issues that were completed
completedIssues <- issues[issues$status %in% completedStatuses, ]

#-----------------------------------------------------------------------------------------------------------------------
#number of issues per week that exceeds 1W and 2W time to complete

#add column with information when particular issue was completed
#LT1W - less then 1 week (168 hours)
#GT1W - between 1 and 2 weeks (336 hours)
#GT2W - greater than 2 weeks
completedIssues$timeToCompleteQuantified <-
  ifelse(
    completedIssues$timeToComplete < 168,
    "LT1W",
    ifelse(
      completedIssues$timeToComplete >= 168 &
        completedIssues$timeToComplete < 336,
      "GT1W",
      "GT2W"
    )
  )

#aggregate by week and time to complete
completedIssuesAggrToC <-
  aggregate(
    x = completedIssues$Quantity,
    by = list(
      completedIssues$EndWeek,
      completedIssues$timeToCompleteQuantified
    ),
    FUN = sum
  )
colnames(completedIssuesAggrToC)[1] <- "week"
colnames(completedIssuesAggrToC)[2] <- "ToC"
colnames(completedIssuesAggrToC)[3] <- "count"

#convert ToC column to factor values
completedIssuesAggrToC$ToC <- factor(completedIssuesAggrToC$ToC,
                                     c("LT1W", "GT1W", "GT2W"))


plot_toC <- ggplot(
  data = completedIssuesAggrToC,
  aes(
    x = completedIssuesAggrToC$week,
    y = completedIssuesAggrToC$count,
    fill = completedIssuesAggrToC$ToC
  )
  
) +
  geom_bar(stat = "identity") +
  ggtitle("Issues reported by source weekly") + scale_fill_manual(values =
                                                                    c("green", "orange", "red")) +
  ylab("Number of issues") +
  xlab("week") + ggtitle(paste("Completed issues weekly in project")) +
  labs(fill = "Type")

ggsave("plot_toC.pdf", plot = plot_toC)

#View(completedIssuesAggrToC)
