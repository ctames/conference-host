###
### Breakout sessions
###   1 (1-6) - Monday, 1:30-3:00pm - opposite Educating Everyone panel
###   2 (7-12) - Tuesday, 1:30-3:00pm - opposite Security and Privacy Challenges in Health Informatics
###   3 (13-18) - Tuesday, 3:30-5:00pm - opposite Future of Privacy panel

BREAKOUTS =  \
   [ (1, 1, 'Potomac 1',
      '1. Cryptocurrency',
      'Cryptocurrency', ['elaine@cs.umd.edu'],
      """
Decentralized crypto-currencies such as Bitcoin have gained rapid
popularity, and have attracted the attention of academics,
entrepreneurs, economists, as well as policy-makers. Crypto-currencies
promise new, automatically enforceable smart contracts that can lower
legal and transactional fees, and create new
markets. Crypto-currencies have become the central playground for
innovation, and will be the way of the future for financial
transactions.  What research challenges do crypto-currencies pose to
the SATC community? Where will crypto-currencies be and where do we
want crypto-currencies to be in the future? How can our research
community help shape the next-generation crypto-currencies? How can we
bring different communities (e.g., scientists, policy-makers,
economists) together to make crypto-currencies better?
"""),
     (2, 1, 'Potomac 2', 
      '2. Crowdsourcing',
      'Social Networks and Crowdsourcing', ['ravenben@cs.ucsb.edu'],
"""
The security of social networks and crowdsourced systems include
topics that directly impact the security and privacy of hundreds of
millions of users. To date, the security community has focused on a
somewhat limited set of problems in this space, focusing on the
detection of Sybil (fake) accounts, spam and fake content (e.g. fake
Yelp reviews).  Key questions of interest to this breakout discussion
might include: (1) what are potential areas of study in the security of
social systems that warrant more attention from the research
community? (2) does malicious crowdsourcing pose a real or hypothetical
threat to online systems? (3) what are current and future obstacles to
productive research in this space (i.e. access to data) and how can we
work together to address them?
"""),
     (3, 1, 'Potomac 3',
      '3. Crypto Assumptions',
      'Cryptographic Assumptions and the Real World', ['tal@cs.columbia.edu'],
      """
Cryptography has made great progress in theoretically sound results
based on formalized assumptions, but when cryptosystems are
implemented and deployed they tend to break in ways not captured by
the cryptographic model. Moreover, recent breakthroughs in
cryptography rely on new intractability assumptions that are poorly
understood and possibly even false. This breakout will look at the gap
between cryptographic assumptions and the real world, and what can be
done to close that gap.
"""),

     (4, 1, 'Potomac 4',
      '4. Benchmarks',
      'Benchmarks for Security Research', ['ezk@cs.sunysb.edu'],
"""
What is the state of benchmarking security systems?  What's been
measured in the past, other than "performance"?  How do you evaluate
security vs. energy, reliability, long-term $cost models, and other
measurable metrics?  What kind of metrics we have/need to compare one
security system vs. another (e.g., how can we say "System X is p% more
secure than system Y)"?  How can we evaluate difficult-to-measure
dimensions such as the absence of security break-ins and usability and
ease-of-use to end-users, IT personnel, and programmers?
"""),
     (5, 1, 'Potomac 5',
      '5. Social Sciences',
      'Cybersecurity and the Social Sciences',
      ['axe@umich.edu'],
"""
What ideas from the social sciences could be useful for cybersecurity
but are not being widely explored, and what can be done to enable
productive collaborations between social scientists and computer
scientists (and others) working on cybersecurity?
"""),

     (6, 1, 'Potomac 6',
      '6. NSA',
      'Responding to the NSA Revelations',
      ['wendy@seltzer.org'],
      """
How should the research community respond to revelations about NSA surveillance and other
activities?
"""),
     (7, 2, 'Potomac 1',
      '7. Experimentation',
      'Cybersecurity Experimentation of the Future: Supporting Research for the Real World', 
      ['david.balenson@sri.com', 'laura.tinnel@sri.com', 'tbenzel@isi.edu'],
      """
This breakout will investigate the current experimentation
infrastructure for cybersecurity research and explore paths forward to
developing an effective cybersecurity experimentation capability that
meets tomorrow's research needs."""
),

###   2 (7-12) - Tuesday, 1:30-3:00pm - opposite Security and Privacy Challenges in Health Informatics
     (8, 2, 'Potomac 2', 
      '8. Principled Curriculum',
      'Developing a Principled Security Curriculum', ['rebecca.wright@rutgers.edu'],
"""
What should a security curriculum cover?  How can we improve how security principles are taught?
"""),
     (9, 2, 'Potomac 3', 
      '9. User Authentication',
'User Authentication', ['nicolasc@andrew.cmu.edu'],
"""
What should the research community do to improve user authentication?
There's a long held belief that passwords don't work well, but no
alternative has succeeded in getting much traction.  Are there
practical ways to improve how passwords are used, or ways to
replace/enhance user authentication that can work in practice?
"""),
     (10, 2, 'Potomac 4', 
      '10. Vulnerabilities',
      'An End to (Silly) Vulnerabilities', ['might@cs.utah.edu'],
"""
In the past year, we've seen billions of systems compromised by
seemingly inexcusable vulnerabilities so notorious they have logos
(e.g., 'goto fail;', Heartbleed, ShellShock).  How do we eliminate
these kinds of vulnerabilities? Is this mostly a problem of technical
research, education, or incentives?
"""
      ),
     (11, 2, 'Potomac 5', 
      '11. Human Factors',
      'Human Factors', ['mccoy@cs.gmu.edu'],
"""
What are unexplored opportunities for research that combines
sociology/criminology/psychology with technical aspects of computing?
"""),
     (12, 2, 'Potomac 6', 
      '12. Architecture',
      'Architecture', ['gs272@cornell.edu', 'rblee@princeton.edu'],
"""
What are the best opportunities today for architecture-focused
security research? What problems in hardware, software and network
security can best be addressed by architectural changes or new
architecture?  How should smartphone, IoT and cloud computing servers
be designed to improve cyber security? How should researchers in
different domains collaborate with architecture researchers on
security problems?
"""),


###   3 (13-18) - Tuesday, 3:30-5:00pm - opposite Future of Privacy panel
     (13, 3, 'Potomac 1',
      '13. Cloud Security',
      'Cloud Security', ['devadas@mit.edu'],
"""
What are the short- and long-term research challenges in cloud
security?  How does the move to the cloud change security and privacy?
"""),
     (14, 3, 'Potomac 2',
      '14. ML',
      'Machine Learning', ['mingyan@eecs.umich.edu'],
      """
What are the opportunities and risks of using machine learning techniques for security classification?  What are good directions for future research for machine learning and security?
"""),
     (15, 3, 'Potomac 3',
      '15. App Markets',
      'App Markets', ['jha@cs.wisc.edu'],
"""
What should the research community in using program analysis to vet
programs in app markets?  What the open research challenges are for
using app markets to improve security and improving the security of app markets?
"""),
     (16, 3, 'Potomac 4',
      '16. Secure Email',
      'Securing the Web for Everyone', ['roxana@cs.columbia.edu'],
"""
Despite lots of technical advances, the typical security and privacy
experience of most web users today is dismal.  What the research
community can do to have immediate and longer-term impacts on privacy
and security for typical web users?  How much of the problem depends
on education, how much can be done with existing solutions, and what
new research is needed?
"""),
     (17, 3, 'Potomac 5',
      '17. Embedded Security',
      'Securing Cyber-Physical Systems', ['stephane@umich.edu'],
"""
How are security and privacy challenges different for computing
systems that interact with the physical world?  What does this mean
for opportunities for future research?
"""),
     (18, 3, 'Potomac 6',
      '18. Competitions',
      'Cybersecurity Competitions', ['edrportia@gmail.com'],
"""
There are many audiences engaged in cybersecurity competitions
including organizers, developers, employers, educators, and
competitors/learners. What outcomes of cybersecurity competitions
could define success for each audience if achieved? How do we measure
and report these outcomes? What challenges must be overcome to achieve
the desired outcomes for the diverse audiences? What cybersecurity
competition activities/tasks need to be investigated which could
support the engagement of diverse audiences?
""")]
